"""1.6 — Storage: round-trip preserves rows, provenance, metadata."""

from app.schemas import Dataset, DatasetRow
from app.storage import Storage


def _make_dataset(session_id: str = "sess-test", dataset_id: str = "d-test") -> Dataset:
    return Dataset(
        dataset_id=dataset_id,
        session_id=session_id,
        name="study_vs_scores",
        rows=[
            DatasetRow(values={"study_hours": 5, "exam_score": 60}, provenance="synthetic"),
            DatasetRow(values={"study_hours": 7, "exam_score": 72}, provenance="synthetic"),
            DatasetRow(values={"study_hours": 9, "exam_score": 81}, provenance="original"),
            DatasetRow(values={"study_hours": 10, "exam_score": 88}, provenance="augmented"),
        ],
        schema={"columns": ["study_hours", "exam_score"]},
        warning="All rows must be labeled synthetic.",
        llm_mode="mock",
        adaption_mode="emulated",
    )


def test_roundtrip_preserves_rows_and_provenance(tmp_path):
    store = Storage(session_dir=tmp_path)
    ds = _make_dataset()
    store.save_dataset(ds)
    loaded = store.load_dataset("d-test")
    assert loaded is not None
    assert len(loaded.rows) == 4
    tags = [r.provenance for r in loaded.rows]
    assert tags == ["synthetic", "synthetic", "original", "augmented"]
    for original, restored in zip(ds.rows, loaded.rows):
        assert original.values == restored.values


def test_metadata_preserved(tmp_path):
    store = Storage(session_dir=tmp_path)
    store.save_dataset(_make_dataset())
    loaded = store.load_dataset("d-test")
    assert loaded.name == "study_vs_scores"
    assert loaded.llm_mode == "mock"
    assert loaded.adaption_mode == "emulated"
    assert loaded.warning == "All rows must be labeled synthetic."


def test_load_missing_returns_none(tmp_path):
    store = Storage(session_dir=tmp_path)
    assert store.load_dataset("nonexistent") is None


def test_receipt_roundtrip(tmp_path):
    from app.schemas import Receipt, ReceiptFields

    store = Storage(session_dir=tmp_path)
    receipt = Receipt(
        receipt_id="r1",
        session_id="s1",
        dataset_id="d1",
        fields=ReceiptFields(
            research_question="q",
            dataset_source="invented",
            ai_tools_used=[{"tool": "llm", "purpose": "generation"}],
            generated_vs_student={"generated": "rows", "student": "plan"},
            timestamp="2026-11-17T09:00:00Z",
            integrity_hash="abc",
        ),
    )
    store.save_receipt(receipt)
    loaded = store.load_receipt("r1")
    assert loaded is not None
    assert loaded.fields.research_question == "q"
