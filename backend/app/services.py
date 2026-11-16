"""
services.py — Phase 2 orchestration for the core data features (F1, F2, F3, F7).

Honesty rules enforced here:
- every generated row is tagged `synthetic`; every augmented row `augmented`
- invalid rows are dropped and logged, never silently "fixed" by invention
- diversity is enforced with a real near-duplicate check; retries change the
  generation pattern (offset), they don't fake diversity
- baseline audits are saved so F4 can show real before/after numbers
"""

from __future__ import annotations

import base64
import binascii
import io
import uuid
from pathlib import Path

import pandas as pd

from . import config, quality
from .adaption import AdaptionClient
from .llm import LLMError, get_llm
from .schemas import AuditReport, Dataset, DatasetRow, Provenance, Receipt, ScopeResult, Variable
from .storage import Storage

MIN_ROWS, MAX_ROWS = 10, 200
MAX_AUGMENT_FACTOR = 5
NEAR_DUP_LIMIT = 0.05
_MAX_TOPUP_ROUNDS = 4


def _dedup_keep_first(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows on VALUE columns only (the provenance tag
    differs between original/augmented), keeping the first occurrence."""
    value_cols = [c for c in df.columns if c != "provenance"]
    keep = ~df.duplicated(subset=value_cols, keep="first")
    return df[keep].reset_index(drop=True)


class ServiceError(Exception):
    """Business-level error with a user-facing message."""


def _template_meta(plan: ScopeResult) -> tuple[dict, dict]:
    """Bounds/allowed-values from the matched template (may be empty)."""
    import json

    for f in config.TEMPLATES_DIR.glob("*.json"):
        tpl = json.loads(f.read_text())
        if tpl.get("dataset_name") == plan.dataset_name or tpl.get("id") == plan.dataset_name:
            return tpl.get("mock_ranges", {}), tpl.get("mock_values", {})
    return {}, {}


# ---------------------------------------------------------------- F1: scope

def scope_question(question: str, refinement: str | None = None) -> tuple[ScopeResult, str]:
    """F1/F7 — parse a question (or a chosen refinement) into a plan."""
    q = (refinement or question).strip()
    if not q:
        raise ServiceError("Question cannot be empty.")
    llm = get_llm()
    try:
        return llm.scope(q)
    except LLMError as e:
        raise ServiceError(f"Scope planning failed: {e}") from e


def _validate_plan(plan: ScopeResult) -> None:
    if plan.suggested_rows <= 0:
        raise ServiceError("Plan must suggest a positive row count.")
    if not plan.variables:
        raise ServiceError("Plan must include at least one variable.")
    for v in plan.variables:
        if not v.name.strip():
            raise ServiceError("Plan variables must have names.")


# ---------------------------------------------------------------- F2: invention

def _row_is_valid(row: DatasetRow, plan: ScopeResult, ranges: dict, allowed: dict) -> bool:
    for var in plan.variables:
        name = var.name
        if name not in row.values:
            return False
        value = row.values[name]
        if var.type == "numeric":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            if name in ranges:
                lo, hi = ranges[name]
                if not (lo <= value <= hi):
                    return False
        elif var.type == "categorical":
            if not isinstance(value, str):
                return False
            if name in allowed and value not in allowed[name]:
                return False
        elif not isinstance(value, str):
            return False
    return True


def invent_dataset(session_id: str, plan: ScopeResult, rows: int) -> Dataset:
    """F2 — generate a synthetic dataset for a plan, validated and diversity-checked."""
    _validate_plan(plan)
    rows = max(MIN_ROWS, min(MAX_ROWS, rows))
    ranges, allowed = _template_meta(plan)

    adaption = AdaptionClient()
    llm = get_llm()
    best: list[DatasetRow] | None = None
    offset = 0
    last_dropped = 0
    last_near_dup = 1.0

    for attempt in range(3):  # generation → validation → diversity, with retries
        rows_out, _ = adaption.invent(plan, rows, offset)
        valid = [r for r in rows_out if _row_is_valid(r, plan, ranges, allowed)]
        dropped = len(rows_out) - len(valid)

        deduped = []
        seen = set()
        for r in valid:
            key = tuple(sorted((k, str(v)) for k, v in r.values.items()))
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        near_dup = quality.near_duplicate_rate(
            pd.DataFrame([r.values for r in deduped])
        ) if deduped else 1.0

        valid_ratio = len(deduped) / rows if rows else 0
        # accept: enough valid rows AND near-dup within limit
        if valid_ratio >= 0.9 and near_dup <= NEAR_DUP_LIMIT:
            best = deduped
            last_dropped, last_near_dup = dropped, near_dup
            break
        offset += 1
        last_dropped, last_near_dup = dropped, near_dup

    if best is None:
        raise ServiceError(
            f"Generation failed quality checks after retries "
            f"(valid ratio < 90% or near-duplicate rate > {NEAR_DUP_LIMIT:.0%})."
        )

    dataset = Dataset(
        dataset_id=f"d_{uuid.uuid4().hex[:8]}",
        session_id=session_id or uuid.uuid4().hex,
        name=plan.dataset_name,
        rows=best,
        schema={
            "columns": [v.name for v in plan.variables],
            "types": {v.name: v.type for v in plan.variables},
        },
        warning=(
            "All rows are synthetic and must be labeled as such in any use. "
            f"Validation: {len(best)}/{rows} rows kept, {last_dropped} dropped, "
            f"near-duplicate rate {last_near_dup:.1%}."
        ),
        llm_mode=llm.mode,
        adaption_mode=adaption.mode,
    )
    Storage().save_dataset(dataset)
    return dataset


# ---------------------------------------------------------------- F3: augmentation
def _decode_csv(csv_b64: str) -> pd.DataFrame:
    try:
        raw = base64.b64decode(csv_b64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ServiceError("Uploaded file is not valid base64 CSV.") from e
    try:
        df = pd.read_csv(pd.io.common.BytesIO(raw))
    except Exception as e:
        raise ServiceError(f"Malformed CSV: could not parse the uploaded file ({e}).") from e
    if df.empty or len(df.columns) == 0:
        raise ServiceError("CSV is empty or has no columns.")
    return df


def augment_dataset(session_id: str, csv_b64: str, target_rows: int, filename: str | None) -> Dataset:
    """F3 — clean a small uploaded CSV and augment it to a target size."""
    df = _decode_csv(csv_b64)
    if target_rows < 1:
        raise ServiceError("target_rows must be at least 1.")

    # baseline (pre-clean) audit — real numbers for F4's before/after
    baseline = quality.audit_dataset(df)

    cleaned, clean_stats = quality.clean_dataset(df)
    n_original = len(cleaned)
    capped_target = min(target_rows, max(n_original, n_original * MAX_AUGMENT_FACTOR), MAX_ROWS)

    adaption = AdaptionClient()
    llm = get_llm()

    if capped_target <= n_original:
        out = cleaned.copy()
        out["provenance"] = "original"
        warning = "No augmentation needed: target size does not exceed the cleaned dataset size."
    else:
        out, _ = adaption.improve(cleaned, capped_target)
        # 5.9 bug-fix: augmentation may introduce exact duplicate rows (variations
        # can collide with each other or with originals). Dedupe, then top up to
        # the target — always preserving the honest original/augmented tagging.
        out = _dedup_keep_first(out)
        for _ in range(_MAX_TOPUP_ROUNDS):
            if len(out) >= capped_target:
                break
            need = capped_target - len(out)
            grown, _ = adaption.improve(out, len(out) + need)
            grown = grown.copy()
            # keep the existing rows' tags; only genuinely new rows are augmented
            n_keep = min(len(out), len(grown))
            grown["provenance"] = (
                out["provenance"].tolist()[:n_keep]
                + ["augmented"] * (len(grown) - n_keep)
            )
            before_len = len(out)
            out = _dedup_keep_first(grown)
            if len(out) == before_len:
                break  # no new unique rows — stop rather than loop forever
        n_aug = sum(1 for p in out["provenance"] if p == "augmented")
        warning = (
            f"Original rows ({len(out) - n_aug}) preserved and tagged 'original'; "
            f"{n_aug} augmented rows are variations and tagged 'augmented'. "
            "Augmented values are small variations of original data — not invented facts."
        )

    # ensure no NaN remains in numeric columns (augmentation must not introduce gaps)
    for col in out.columns:
        if col == "provenance":
            continue
        if pd.api.types.is_numeric_dtype(out[col]) and out[col].isna().any():
            out[col] = out[col].fillna(out[col].median())

    dataset = Dataset(
        dataset_id=f"d_{uuid.uuid4().hex[:8]}",
        session_id=session_id or uuid.uuid4().hex,
        name=Path(filename).stem if filename else "augmented_dataset",
        rows=[
            DatasetRow(
                values={c: v for c, v in row.items() if c != "provenance"},
                provenance=row["provenance"],
            )
            for row in out.to_dict(orient="records")
        ],
        schema={"columns": [c for c in out.columns if c != "provenance"]},
        warning=warning,
        llm_mode=llm.mode,
        adaption_mode=adaption.mode,
    )
    store = Storage()
    store.save_dataset(dataset)
    store.save_baseline_audit(dataset.dataset_id, dataset.session_id, baseline)
    return dataset


# ---------------------------------------------------------------- F4: audit (before/after)

# metric → whether higher values are better (for verdict wording)
_HIGHER_IS_BETTER = {
    "duplicate_rate": False,
    "near_duplicate_rate": False,
    "diversity": False,
    "completeness": True,
    "label_coverage": True,
}


def _verdict_word(before: float, after: float, higher_is_better: bool) -> str:
    if before == after:
        return "held"
    improved = after > before if higher_is_better else after < before
    return "improved" if improved else "worsened"


def audit_dataset(dataset_id: str) -> AuditReport:
    """F4 — real metrics on the current dataset, paired with the baseline
    (pre-clean/pre-augment) when one exists, plus plain-language interpretation."""
    store = Storage()
    dataset = store.load_dataset(dataset_id)
    if dataset is None:
        raise ServiceError("Dataset not found.")

    df = pd.DataFrame([r.values for r in dataset.rows])
    current = quality.audit_dataset(df)
    baseline = store.load_baseline_audit(dataset_id)

    metrics: dict = {}
    for key, after_val in current.items():
        if key == "distribution_sanity":
            metrics[key] = after_val
            continue
        before_val = baseline.get(key) if baseline else after_val
        entry = {"before": before_val, "after": after_val}
        if baseline is None:
            entry["note"] = "no baseline stored — values reflect the current dataset only"
        metrics[key] = entry

    interpretations: list[str] = []
    for key in _HIGHER_IS_BETTER:
        entry = metrics.get(key)
        if not entry or "before" not in entry:
            continue
        before, after = entry["before"], entry["after"]
        if before is None or after is None:
            continue
        word = _verdict_word(float(before), float(after), _HIGHER_IS_BETTER[key])
        better = "higher is better" if _HIGHER_IS_BETTER[key] else "lower is better"
        interpretations.append(
            f"{key.replace('_', ' ').capitalize()}: {float(before):.3f} → {float(after):.3f} "
            f"({word}; {better})."
        )

    sanity = metrics.get("distribution_sanity", {})
    if sanity and not sanity.get("passed", True):
        interpretations.append(f"Distribution sanity: issues found — {', '.join(sanity.get('issues', []))}.")
    else:
        interpretations.append("Distribution sanity: no structural issues in numeric columns.")

    changed = sum(
        1 for k in _HIGHER_IS_BETTER
        if "before" in metrics.get(k, {}) and metrics[k]["before"] != metrics[k]["after"]
    )
    if baseline is None:
        interpretations.append(
            "Overall: no baseline audit was stored for this dataset, so the audit reflects "
            "the current dataset only."
        )
    elif changed:
        interpretations.append(
            f"Overall: {changed} metric(s) changed between baseline and current state — "
            "see the before/after values above."
        )
    else:
        interpretations.append("Overall: all metrics held steady between baseline and current state.")

    return AuditReport(dataset_id=dataset_id, metrics=metrics, interpretation=interpretations)


# ---------------------------------------------------------------- F11: contribution log

def log_contribution(session_id: str, action: str, detail: str = "") -> None:
    """F11 — record a student action (plan edits, row corrections, ...)."""
    if not action.strip():
        raise ServiceError("Contribution action cannot be empty.")
    Storage().log_contribution(session_id, action.strip(), detail)


def _record_student_action(session_id: str | None, action: str, detail: str = "") -> None:
    """Best-effort student-action recording from endpoint flows (F11)."""
    if session_id:
        Storage().log_contribution(session_id, action, detail)


# ---------------------------------------------------------------- 3.10: methodology draft

def draft_methodology(session_id: str, dataset: Dataset) -> tuple[str, str]:
    """Draft a short methodology paragraph from the plan + dataset. Never
    overclaims: mode and the absence of sources are stated explicitly."""
    store = Storage()
    meta = store.load_session_meta(session_id) or {}
    plan_data = meta.get("plan")
    if plan_data:
        try:
            plan = ScopeResult(**plan_data)
        except Exception:
            plan = None
    else:
        plan = None
    if plan is None:
        # fallback: reconstruct a minimal plan from the dataset schema
        schema = dataset.schema_ or {}
        plan = ScopeResult(
            research_type="descriptive",
            variables=[Variable(name=c, type="numeric") for c in schema.get("columns", [])],
            suggested_rows=len(dataset.rows),
            data_plan=f"Dataset '{dataset.name}' with columns: {', '.join(schema.get('columns', []))}.",
            dataset_name=dataset.name,
            refinements=[],
        )
    note = (
        "No external sources were consulted for this draft. "
        f"The dataset was generated with LLM mode '{dataset.llm_mode}'."
    )
    llm = get_llm()
    try:
        text, mode = llm.draft_methodology(plan, len(dataset.rows), note)
    except LLMError as e:
        raise ServiceError(f"Methodology draft failed: {e}") from e
    return text, mode


def _methodology_markdown(text: str, dataset: Dataset, llm_mode: str, adaption_mode: str) -> str:
    counts = {}
    for r in dataset.rows:
        counts[r.provenance.value] = counts.get(r.provenance.value, 0) + 1
    counts_str = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    return (
        f"# Methodology — {dataset.name}\n\n"
        f"{text}\n\n"
        f"## Dataset provenance\n\n"
        f"- Rows: {len(dataset.rows)} ({counts_str})\n"
        f"- LLM mode: {llm_mode} · Adaption mode: {adaption_mode}\n"
        f"- Every row carries a `provenance` label (synthetic / original / augmented).\n"
    )


# ---------------------------------------------------------------- F6: export bundle

def build_export(session_id: str) -> dict:
    """F6 — bundle dataset.csv + receipt.json + methodology.md for a session.

    Bundles the most recent dataset in the session (the final state of the
    demo flow). Receipt is built (standard variant) if none exists yet.
    """
    store = Storage()
    index = store._read_index()
    datasets = [d_id for d_id, entry in index["datasets"].items() if entry["session_id"] == session_id]
    if not datasets:
        raise ServiceError("No datasets found in this session — nothing to export.")
    dataset_id = datasets[-1]  # latest dataset in the session
    dataset = store.load_dataset(dataset_id)
    if dataset is None:
        raise ServiceError(f"Latest dataset could not be loaded: {dataset_id}")

    # receipt: build one if the session has none for this dataset
    receipts = [r_id for r_id, entry in index["receipts"].items() if entry["session_id"] == session_id]
    if not receipts:
        receipt = build_receipt_safe(session_id, dataset_id)
        receipt_json = receipt.model_dump_json(indent=2)
    else:
        receipt = store.load_receipt(receipts[-1])
        receipt_json = Path(store._session_dir(session_id) / "receipts" / f"{receipts[-1]}.json").read_text()

    methodology_text, _ = draft_methodology(session_id, dataset)
    methodology_md = _methodology_markdown(methodology_text, dataset, dataset.llm_mode, dataset.adaption_mode)

    # dataset CSV with provenance column preserved
    csv_buf = io.StringIO()
    pd.DataFrame([{**r.values, "provenance": r.provenance.value} for r in dataset.rows]).to_csv(csv_buf, index=False)
    csv_text = csv_buf.getvalue()

    files = {"dataset.csv": csv_text, "receipt.json": receipt_json, "methodology.md": methodology_md}
    export_dir = store._session_dir(session_id) / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (export_dir / name).write_text(content)

    return {
        "session_id": session_id,
        "dataset_id": dataset_id,
        "files": {name: f"/api/exports/{session_id}/{name}" for name in files},
    }


def build_receipt_safe(session_id: str, dataset_id: str) -> Receipt:
    """Receipt builder wrapper that turns ValueError into ServiceError."""
    from .receipt import build_receipt

    dataset = Storage().load_dataset(dataset_id)
    if dataset is None:
        raise ServiceError(f"Dataset not found: {dataset_id}")
    source = _dataset_source(dataset)
    try:
        return build_receipt(session_id, dataset_id, source)
    except ValueError as e:
        raise ServiceError(str(e)) from e


def _dataset_source(dataset: Dataset) -> str:
    counts = {}
    for r in dataset.rows:
        counts[r.provenance.value] = counts.get(r.provenance.value, 0) + 1
    if counts.get("augmented", 0) > 0:
        return "augmented"
    if counts.get("synthetic", 0) == len(dataset.rows):
        return "invented"
    return "uploaded"
