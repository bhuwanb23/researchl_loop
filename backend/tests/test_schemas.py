"""1.2 — schemas: contracts match docs/05; provenance enum enforced."""

import pytest
from pydantic import ValidationError

from app.schemas import Dataset, DatasetRow, Receipt, ReceiptFields, ScopeResult, Variable


def test_scope_result_requires_contract_fields():
    scope = ScopeResult(
        research_type="regression",
        variables=[Variable(name="study_hours", type="numeric", unit="hours")],
        suggested_rows=80,
        data_plan="Generate records",
        dataset_name="study_vs_scores",
    )
    assert scope.research_type == "regression"
    assert scope.variables[0].name == "study_hours"


def test_scope_result_rejects_invalid_research_type():
    with pytest.raises(ValidationError):
        ScopeResult(
            research_type="nonsense",
            variables=[Variable(name="x", type="numeric")],
            suggested_rows=10,
            data_plan="x",
            dataset_name="x",
        )


def test_dataset_row_provenance_enum_enforced():
    with pytest.raises(ValidationError):
        DatasetRow(values={"a": 1}, provenance="unknown")  # type: ignore[arg-type]


def test_dataset_row_valid_provenance():
    row = DatasetRow(values={"a": 1}, provenance="synthetic")
    assert row.provenance == "synthetic"


def test_receipt_requires_fields():
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
    assert receipt.fields.human_oversight_level == "prompt_guided"  # C2PA default


def test_dataset_model_roundtrips():
    ds = Dataset(
        dataset_id="d1",
        session_id="s1",
        name="n",
        rows=[DatasetRow(values={"a": 1}, provenance="original")],
        schema={},
        warning="w",
        llm_mode="mock",
        adaption_mode="emulated",
    )
    ds2 = Dataset(**ds.model_dump())
    assert ds2.rows[0].provenance == "original"
