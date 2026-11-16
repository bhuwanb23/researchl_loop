"""
storage.py — session/dataset/receipt storage for ResearchLoop.

Layout (docs/05, Phase 1 feature behavior):
    data/sessions/{session_id}/{dataset_id}/rows.csv        (values + provenance column)
    data/sessions/{session_id}/{dataset_id}/metadata.json   (schema, modes, provenance counts)
    data/sessions/{session_id}/session.json                 (question, plan — F5/F6 context)
    data/sessions/{session_id}/contributions.json           (F11 student action log)
    data/sessions/{session_id}/exports/                     (F6 export bundle files)
    data/sessions/index.json                                (dataset_id / receipt_id -> path)

Provenance is stored IN the CSV and restored on load — round-trips preserve
the honesty rule.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config
from .schemas import Dataset, DatasetRow, Provenance, Receipt


class Storage:
    def __init__(self, session_dir: Path | None = None):
        self.session_dir = session_dir or config.SESSION_DIR

    # ----- index

    def _index_path(self) -> Path:
        return self.session_dir / "index.json"

    def _read_index(self) -> dict:
        if self._index_path().exists():
            return json.loads(self._index_path().read_text())
        return {"datasets": {}, "receipts": {}}

    def _write_index(self, index: dict) -> None:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._index_path().write_text(json.dumps(index, indent=2))

    # ----- datasets

    def _dataset_dir(self, session_id: str, dataset_id: str) -> Path:
        return self.session_dir / session_id / dataset_id

    def save_dataset(self, dataset: Dataset) -> None:
        d = self._dataset_dir(dataset.session_id, dataset.dataset_id)
        d.mkdir(parents=True, exist_ok=True)
        rows = [{**r.values, "provenance": r.provenance.value} for r in dataset.rows]
        pd.DataFrame(rows).to_csv(d / "rows.csv", index=False)
        metadata = dataset.model_dump(mode="json", by_alias=True)
        metadata.pop("rows", None)
        metadata["row_count"] = len(dataset.rows)
        metadata["provenance_counts"] = {
            p.value: sum(1 for r in dataset.rows if r.provenance == p) for p in Provenance
        }
        (d / "metadata.json").write_text(json.dumps(metadata, indent=2))

        index = self._read_index()
        index["datasets"][dataset.dataset_id] = {
            "session_id": dataset.session_id,
            "name": dataset.name,
        }
        self._write_index(index)

    def load_dataset(self, dataset_id: str) -> Dataset | None:
        index = self._read_index()
        entry = index["datasets"].get(dataset_id)
        if not entry:
            return None
        d = self._dataset_dir(entry["session_id"], dataset_id)
        rows_df = pd.read_csv(d / "rows.csv")
        rows = [
            DatasetRow(
                values={c: v for c, v in row.items() if c != "provenance"},
                provenance=row["provenance"],
            )
            for row in rows_df.to_dict(orient="records")
        ]
        metadata = json.loads((d / "metadata.json").read_text())
        return Dataset(
            dataset_id=dataset_id,
            session_id=entry["session_id"],
            name=metadata.get("name", dataset_id),
            rows=rows,
            schema=metadata.get("schema", {}),
            warning=metadata.get("warning"),
            llm_mode=metadata.get("llm_mode", "mock"),
            adaption_mode=metadata.get("adaption_mode", "emulated"),
        )

    # ----- receipts

    def save_receipt(self, receipt: Receipt) -> None:
        d = self.session_dir / receipt.session_id / "receipts"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json(indent=2))
        index = self._read_index()
        index["receipts"][receipt.receipt_id] = {"session_id": receipt.session_id}
        self._write_index(index)

    def load_receipt(self, receipt_id: str) -> Receipt | None:
        index = self._read_index()
        entry = index["receipts"].get(receipt_id)
        if not entry:
            return None
        path = self.session_dir / entry["session_id"] / "receipts" / f"{receipt_id}.json"
        if not path.exists():
            return None
        return Receipt(**json.loads(path.read_text()))

    # ----- session meta + contribution log (F5 context / F11)

    def _session_dir(self, session_id: str) -> Path:
        return self.session_dir / session_id

    def save_session_meta(self, session_id: str, meta: dict) -> None:
        d = self._session_dir(session_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / "session.json").write_text(json.dumps(meta, indent=2))

    def load_session_meta(self, session_id: str) -> dict | None:
        path = self._session_dir(session_id) / "session.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def log_contribution(self, session_id: str, action: str, detail: str = "") -> None:
        """F11 — record a student action in the session's contribution log."""
        path = self._session_dir(session_id) / "contributions.json"
        entries: list[dict] = []
        if path.exists():
            entries = json.loads(path.read_text())
        entries.append({
            "action": action,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._session_dir(session_id).mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2))

    def get_contributions(self, session_id: str) -> list[dict]:
        path = self._session_dir(session_id) / "contributions.json"
        if not path.exists():
            return []
        return json.loads(path.read_text())

    # ----- baseline audits (F3: keep the pre-augment state for F4 before/after)

    def save_baseline_audit(self, dataset_id: str, session_id: str, report: dict) -> None:
        d = self._dataset_dir(session_id, dataset_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / "baseline_audit.json").write_text(json.dumps(report, indent=2))

    def load_baseline_audit(self, dataset_id: str) -> dict | None:
        index = self._read_index()
        entry = index["datasets"].get(dataset_id)
        if not entry:
            return None
        path = self._dataset_dir(entry["session_id"], dataset_id) / "baseline_audit.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())
