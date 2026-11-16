"""
llm.py — ResearchLoop LLM layer: one interface, two implementations.

- MockLLM: deterministic, template-driven fallback. Works offline, always.
- RealLLM: OpenAI-compatible endpoint (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL).

Every method returns (payload, mode) so downstream code (receipt, UI) always
knows which implementation actually ran. Nothing downstream ever assumes real
generation happened — this is the honesty mechanism.

MockLLM never fabricates sources; RealLLM prompts explicitly forbid them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from ..core import config
from ..core.schemas import DatasetRow, ScopeResult, Variable


class LLMError(Exception):
    """Raised when a real LLM call fails or returns invalid output."""


# ---------------------------------------------------------------- templates

_TEMPLATES: dict[str, dict] = {}


def _load_templates() -> dict[str, dict]:
    if not _TEMPLATES:
        for f in config.TEMPLATES_DIR.glob("*.json"):
            data = json.loads(f.read_text())
            _TEMPLATES[data["id"]] = data
    return _TEMPLATES


def _match_template(question: str) -> dict | None:
    """Best-effort template match by token overlap with template questions."""
    templates = _load_templates()
    question_tokens = {t for t in question.lower().split() if len(t) >= 4}
    best, best_score = None, 0
    for tpl in templates.values():
        tpl_tokens = {t for t in tpl.get("question", "").lower().split() if len(t) >= 4}
        score = len(question_tokens & tpl_tokens)
        if score > best_score:
            best, best_score = tpl, score
    return best if best_score >= 2 else None


# ---------------------------------------------------------------- MockLLM

class MockLLM:
    """Deterministic, offline, template-driven implementation."""

    mode = "mock"

    def scope(self, question: str) -> tuple[ScopeResult, str]:
        tpl = _match_template(question)
        if tpl is not None:
            scope = ScopeResult(
                research_type=tpl["research_type"],
                variables=[Variable(**v) for v in tpl["variables"]],
                suggested_rows=tpl["suggested_rows"],
                data_plan=tpl["data_plan"],
                dataset_name=tpl["dataset_name"],
                refinements=tpl.get("refinements", []),
            )
            return scope, self.mode
        # generic deterministic fallback for free questions
        words = [w for w in question.split() if len(w) >= 4][:3]
        name = "_".join(words).lower() or "research"
        return (
            ScopeResult(
                research_type="descriptive",
                variables=[Variable(name="observation", type="numeric")],
                suggested_rows=50,
                data_plan=f"Generate a synthetic dataset of observations relevant to: {question}",
                dataset_name=name,
                refinements=[f"Reframe the question with a specific measurable variable: {question}"],
            ),
            self.mode,
        )

    def invent(self, plan: ScopeResult, rows: int, offset: int = 0) -> tuple[list[DatasetRow], str]:
        """offset>0 produces a different but still deterministic value pattern —
        used by diversity retries (services) when a generated set is too similar."""
        tpl = _TEMPLATES.get(plan.dataset_name, {})
        ranges = tpl.get("mock_ranges", {})
        values = tpl.get("mock_values", {})
        out: list[DatasetRow] = []
        for i in range(rows):
            record: dict = {}
            for var in plan.variables:
                if var.type == "numeric":
                    lo, hi = ranges.get(var.name, (0, 100))
                    if isinstance(lo, int) and isinstance(hi, int) and (hi - lo) <= 50:
                        record[var.name] = lo + ((i * 7 + offset * 13) % (hi - lo + 1))
                    else:
                        record[var.name] = round(lo + (((i * 13) + (offset * 29)) % 1000) / 1000.0 * (hi - lo), 2)
                elif var.type == "categorical":
                    options = values.get(var.name) or ["Category A", "Category B", "Category C"]
                    record[var.name] = options[(i + offset) % len(options)]
                else:
                    record[var.name] = f"{var.name}_{i}"
            out.append(DatasetRow(values=record, provenance="synthetic"))
        return out, self.mode

    def augment(self, df: pd.DataFrame, target_rows: int) -> tuple[pd.DataFrame, str]:
        n = len(df)
        if target_rows <= n:
            df = df.copy()
            df["provenance"] = "original"
            return df, self.mode
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        object_cols = [c for c in df.columns if c not in numeric_cols]
        new_rows = []
        for i in range(n, target_rows):
            base = df.iloc[i % n]
            row = {}
            for c in numeric_cols:
                # deterministic, near-unique variation: hash-seeded offset in [-0.5, 0.5]
                h = hashlib.sha256(f"{c}:{i}".encode()).hexdigest()
                offset = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1  # -1..1
                row[c] = round(float(base[c]) + offset * 0.5, 2)
            for c in object_cols:
                row[c] = base[c]
            new_rows.append(row)
        augmented = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        augmented["provenance"] = ["original"] * n + ["augmented"] * (len(augmented) - n)
        return augmented, self.mode

    def draft_methodology(self, plan: ScopeResult, n_rows: int, note: str) -> tuple[str, str]:
        text = (
            f"This study addresses the research question: \"{plan.data_plan.split('.')[0] if plan.data_plan else ''}\" "
            f"using a dataset of {n_rows} records covering the variables: "
            f"{', '.join(v.name for v in plan.variables)}. "
            f"The dataset was produced with the ResearchLoop assistant in **{self.mode} mode**; "
            f"{note} Every record carries a provenance label, and no external sources were consulted "
            f"for this draft. Limitations: findings derived from this dataset should be validated "
            f"against real-world data before drawing conclusions."
        )
        return text, self.mode


# ---------------------------------------------------------------- RealLLM

class RealLLM:
    """OpenAI-compatible client. Raises LLMError on any failure — never
    silently degrades to mock (that would be dishonest)."""

    mode = "real"

    def __init__(self, base_url: str, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(base_url=base_url or None, api_key=api_key)
        self._model = model

    def _chat_json(self, system: str, user: str) -> dict:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:  # noqa: BLE001 — wrapped for honest error reporting
            raise LLMError(f"LLM call failed: {e}") from e

    def scope(self, question: str) -> tuple[ScopeResult, str]:
        data = self._chat_json(
            "You are ResearchLoop's scope planner. Given a student research question, return JSON with: "
            "research_type (one of classification, regression, descriptive, survey), variables "
            "(list of {name, type, unit}), suggested_rows (integer 40-100), data_plan (string), "
            "dataset_name (snake_case), refinements (list of 2 alternative questions).",
            question,
        )
        try:
            return ScopeResult(**data), self.mode
        except Exception as e:
            raise LLMError(f"LLM scope output invalid: {e}") from e

    def invent(self, plan: ScopeResult, rows: int, offset: int = 0) -> tuple[list[DatasetRow], str]:
        data = self._chat_json(
            "You generate a synthetic dataset for a student research project. Return JSON: "
            "{\"rows\": [{\"values\": {...}, \"provenance\": \"synthetic\"}]} with exactly the requested "
            "number of rows, matching the variable names and plausible ranges. Maximize diversity: "
            "no copy-paste rows, varied values. Do not include any external sources or references. "
            "All rows must be labeled synthetic.",
            f"Plan: {plan.model_dump_json()} | rows: {rows} | diversity_attempt: {offset}",
        )
        rows_out = data.get("rows", [])
        try:
            return [DatasetRow(**r) for r in rows_out], self.mode
        except Exception as e:
            raise LLMError(f"LLM invent output invalid: {e}") from e

    def augment(self, df: pd.DataFrame, target_rows: int) -> tuple[pd.DataFrame, str]:
        head = df.head(20).to_json(orient="records")
        data = self._chat_json(
            "You augment a small student dataset to a target size. Return JSON: "
            "{\"rows\": [{\"values\": {...}, \"provenance\": \"original\"|\"augmented\"}]}. "
            "Keep the original rows' values; new rows are variations within the same ranges. "
            "Do not invent external facts.",
            f"Dataset head: {head} | target_rows: {target_rows}",
        )
        rows_out = data.get("rows", [])
        try:
            parsed = [DatasetRow(**r) for r in rows_out]
        except Exception as e:
            raise LLMError(f"LLM augment output invalid: {e}") from e
        return pd.DataFrame([r.values for r in parsed]), self.mode

    def draft_methodology(self, plan: ScopeResult, n_rows: int, note: str) -> tuple[str, str]:
        data = self._chat_json(
            "Write a 3-4 sentence research methodology summary for a student project. "
            "Do NOT include any external sources, references, or citations. "
            "Return JSON: {\"text\": \"...\"}",
            f"Plan: {plan.model_dump_json()} | rows: {n_rows} | note: {note}",
        )
        return data.get("text", ""), self.mode


def get_llm():
    """Return the configured LLM implementation (mode reflects reality)."""
    if config.llm_mode() == "real":
        return RealLLM(config.LLM_BASE_URL, config.LLM_API_KEY, config.LLM_MODEL)
    return MockLLM()
