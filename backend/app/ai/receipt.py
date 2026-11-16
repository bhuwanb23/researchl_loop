"""
receipt.py — F5 disclosure receipt builder.

The receipt is generated from *actual run state*: which LLM mode ran, which
Adaption mode ran, what was generated vs. what the student supplied, the
student contribution log (F11), and sources consulted (F9 — empty unless
genuinely consulted; this pipeline never consults sources, so the list is
honestly empty in every mode).

Honesty gates enforced here:
- `ai_tools_used` names the real modes (`llm-mock`, `adaption-emulated`, ...)
- `sources_consulted` is never fabricated — empty unless the run recorded one
- `human_oversight_level` is always `prompt_guided` (never `fully_autonomous`)
- `integrity_hash` is SHA-256 over the canonical JSON of the fields payload
  (excluding the hash itself) — verifiable on reload
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from ..core import config
from ..core.schemas import Dataset, HumanOversight, Receipt, ReceiptFields
from ..core.storage import Storage

VALID_VARIANTS = {"standard", "journal-style", "teacher-check"}


def compute_integrity_hash(payload: dict) -> str:
    """SHA-256 over canonical JSON of the receipt fields payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ai_tools_used(llm_mode: str, adaption_mode: str) -> list[dict[str, str]]:
    """Mode-accurate tool list — names the implementations that actually ran."""
    return [
        {
            "tool": f"llm-{llm_mode}",
            "purpose": "question parsing, dataset generation, methodology draft",
        },
        {
            "tool": f"adaption-{adaption_mode}",
            "purpose": "adaptive data invention and augmentation",
        },
    ]


def _provenance_counts(dataset: Dataset) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in dataset.rows:
        counts[r.provenance.value] = counts.get(r.provenance.value, 0) + 1
    return counts


def _generated_vs_student(dataset: Dataset, contributions: list[dict]) -> dict[str, str]:
    counts = _provenance_counts(dataset)
    count_str = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    generated = (
        f"{len(dataset.rows)} rows generated ({count_str}) via "
        f"llm={dataset.llm_mode}, adaption={dataset.adaption_mode}"
    )
    if contributions:
        actions = sorted({c["action"] for c in contributions})
        student = f"{len(contributions)} logged student actions ({', '.join(actions)})"
    else:
        student = "no student actions logged"
    return {"generated": generated, "student": student}


def build_receipt(
    session_id: str, dataset_id: str, source: str, variant: str = "standard"
) -> Receipt:
    """Build + store a disclosure receipt from the actual run state."""
    if variant not in VALID_VARIANTS:
        raise ValueError(f"Unknown receipt variant '{variant}'. Valid: {sorted(VALID_VARIANTS)}")

    store = Storage()
    dataset = store.load_dataset(dataset_id)
    if dataset is None:
        raise ValueError(f"Dataset not found: {dataset_id}")

    meta = store.load_session_meta(session_id) or {}
    research_question = meta.get("question", "")
    contributions = store.get_contributions(session_id)

    # Fields payload (every contract field). sources_consulted stays empty:
    # this pipeline never consults external sources — fabricating any would
    # violate the honesty gate (F9, docs/06).
    fields_payload: dict = {
        "research_question": research_question,
        "dataset_source": source,
        "ai_tools_used": _ai_tools_used(dataset.llm_mode, dataset.adaption_mode),
        "generated_vs_student": _generated_vs_student(dataset, contributions),
        "human_oversight_level": HumanOversight.PROMPT_GUIDED.value,
        "student_contributions": contributions,
        "sources_consulted": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    fields_payload["integrity_hash"] = compute_integrity_hash(fields_payload)

    receipt = Receipt(
        receipt_id=f"r_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        dataset_id=dataset_id,
        fields=ReceiptFields(**fields_payload),
        format="json",
        variant=variant,
    )
    store.save_receipt(receipt)
    return receipt


def verify_integrity(receipt: Receipt) -> bool:
    """Recompute the hash from the stored fields and compare."""
    payload = receipt.fields.model_dump(mode="json")
    stored = payload.pop("integrity_hash")
    return compute_integrity_hash(payload) == stored


def render_variant(receipt: Receipt, variant: str | None = None) -> dict:
    """F8 — present the same receipt content in different layouts."""
    variant = variant or receipt.variant
    f = receipt.fields
    tools = ", ".join(f"{t['tool']} ({t['purpose']})" for t in f.ai_tools_used)
    if variant == "journal-style":
        return {
            "variant": "journal-style",
            "layout": "COPE/Nature-style disclosure statement",
            "sections": {
                "1. Research question": f.research_question,
                "2. Dataset provenance": f"Source: {f.dataset_source}; {len(f.student_contributions)} student contributions logged.",
                "3. AI tools used": tools,
                "4. Human oversight": f"{f.human_oversight_level} — the student prompted, reviewed, and directed all AI output.",
                "5. Sources consulted": f.sources_consulted or ["none"],
                "6. Integrity": f.integrity_hash,
                "7. Timestamp": f.timestamp,
            },
        }
    if variant == "teacher-check":
        return {
            "variant": "teacher-check",
            "layout": "one-page teacher review sheet",
            "sections": {
                "What the student researched": f.research_question,
                "What AI did": f.generated_vs_student["generated"],
                "What the student did": f.generated_vs_student["student"],
                "Oversight": f.human_oversight_level,
                "Sources used": "none" if not f.sources_consulted else f.sources_consulted,
                "Integrity hash": f.integrity_hash,
            },
        }
    # standard
    return {
        "variant": "standard",
        "layout": "plain disclosure receipt",
        "sections": {
            "research_question": f.research_question,
            "dataset_source": f.dataset_source,
            "ai_tools_used": f.ai_tools_used,
            "generated_vs_student": f.generated_vs_student,
            "human_oversight_level": f.human_oversight_level,
            "student_contributions": f.student_contributions,
            "sources_consulted": f.sources_consulted,
            "timestamp": f.timestamp,
            "integrity_hash": f.integrity_hash,
        },
    }
