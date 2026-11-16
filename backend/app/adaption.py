"""
adaption.py — Adaption Labs adapter (Adaptive Data: invent / improve).

- real mode: calls the Adaption API (requires ADAPTION_API_BASE + ADAPTION_API_KEY).
  NOTE: the exact endpoint path below is a best-effort default and must be
  confirmed against Adaption's API docs once credentials are available. If the
  call fails, AdaptionError is raised — never a silent pretend-real run.
- emulated mode: runs the same workflow semantics locally (generate-where-none-
  exists / clean-augment) through the LLM layer, and labels the output "emulated".

The receipt (Phase 3) records which mode actually ran.
"""

from __future__ import annotations

import pandas as pd

from . import config, quality
from .llm import get_llm
from .schemas import ScopeResult


class AdaptionError(Exception):
    """Raised when a real Adaption call is not configured or fails."""


class AdaptionClient:
    def __init__(self):
        self.mode = config.adaption_mode()
        self._base = config.ADAPTION_API_BASE
        self._key = config.ADAPTION_API_KEY
        self._llm = get_llm()

    # ----- invent (F2: generate data where none exists)

    def invent(self, plan: ScopeResult, rows: int, offset: int = 0) -> tuple[list, str]:
        if self.mode == "emulated":
            rows_out, _ = self._llm.invent(plan, rows, offset)
            return rows_out, "emulated"
        payload, mode = self._call_real("invent", {"plan": plan.model_dump(), "rows": rows})
        return payload, mode

    # ----- improve (F3: clean + augment a tiny dataset)

    def improve(self, df: pd.DataFrame, target_rows: int) -> tuple[pd.DataFrame, str]:
        if self.mode == "emulated":
            cleaned, _ = quality.clean_dataset(df)
            augmented, _ = self._llm.augment(cleaned, target_rows)
            return augmented, "emulated"
        payload, mode = self._call_real("improve", {"rows": df.to_json(orient="records"),
                                                   "target_rows": target_rows})
        return pd.DataFrame(payload["rows"]), mode

    # ----- real path

    def _call_real(self, op: str, payload: dict) -> tuple[dict, str]:
        if not (self._base and self._key):
            raise AdaptionError(
                "Adaption real mode requires ADAPTION_API_BASE and ADAPTION_API_KEY "
                "(fall back to ADAPTION_MODE=emulated)."
            )
        import httpx

        try:
            resp = httpx.post(
                f"{self._base.rstrip('/')}/api/v1/adaptive-data/{op}",
                json=payload,
                headers={"Authorization": f"Bearer {self._key}"},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json(), "real"
        except Exception as e:
            raise AdaptionError(f"Adaption API call failed: {e}") from e
