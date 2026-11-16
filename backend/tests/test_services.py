"""2.1–2.8 — service-level unit tests: scope validation, row validation,
diversity enforcement, refinement flow, augment logic, error paths."""

import base64
import io

import pandas as pd
import pytest

from app import quality, services
from app.llm import MockLLM
from app.schemas import ScopeResult, Variable
from app.storage import Storage

QUESTIONS = {
    "study_vs_scores": "Does study time affect exam scores?",
    "plant_heat_tolerance": "Which local plant species tolerates heat best?",
    "group_study": "Do students who study in groups score higher?",
}


def _scope(question: str) -> ScopeResult:
    scope, mode = MockLLM().scope(question)
    assert mode == "mock"
    return scope


def test_scope_validation_rejects_empty_question():
    with pytest.raises(services.ServiceError):
        services.scope_question("   ")


def test_scope_validation_rejects_bad_plan():
    plan = ScopeResult(
        research_type="descriptive",
        variables=[Variable(name="x", type="numeric")],
        suggested_rows=0,
        data_plan="x",
        dataset_name="x",
    )
    with pytest.raises(services.ServiceError):
        services.invent_dataset("s", plan, 50)


def test_row_validation_drops_out_of_range_and_unknown_categories():
    plan = _scope(QUESTIONS["study_vs_scores"])
    ranges, allowed = services._template_meta(plan)
    good = services.DatasetRow(
        values={"study_hours": 5, "prior_gpa": 3.0, "sleep_hours": 7, "exam_score": 70},
        provenance="synthetic",
    )
    bad_range = services.DatasetRow(
        values={"study_hours": 999, "prior_gpa": 3.0, "sleep_hours": 7, "exam_score": 70},
        provenance="synthetic",
    )
    bad_type = services.DatasetRow(
        values={"study_hours": "five", "prior_gpa": 3.0, "sleep_hours": 7, "exam_score": 70},
        provenance="synthetic",
    )
    missing_col = services.DatasetRow(
        values={"study_hours": 5, "prior_gpa": 3.0, "sleep_hours": 7},
        provenance="synthetic",
    )
    valid = [r for r in (good, bad_range, bad_type, missing_col)
             if services._row_is_valid(r, plan, ranges, allowed)]
    assert valid == [good]


def test_invent_dataset_tags_all_synthetic_and_warning():
    plan = _scope(QUESTIONS["group_study"])
    ds = services.invent_dataset("sess-unit", plan, 80)
    assert len(ds.rows) == 80
    assert all(r.provenance == "synthetic" for r in ds.rows)
    assert ds.warning and "synthetic" in ds.warning
    assert ds.llm_mode == "mock" and ds.adaption_mode == "emulated"
    # stored and loadable
    assert Storage().load_dataset(ds.dataset_id) is not None


def test_invent_dataset_diversity_enforced():
    plan = _scope(QUESTIONS["study_vs_scores"])
    ds = services.invent_dataset("sess-div", plan, 120)
    near_dup = quality.near_duplicate_rate(pd.DataFrame([r.values for r in ds.rows]))
    assert near_dup <= 0.05, f"near-duplicate rate too high: {near_dup}"


def test_invent_row_cap():
    plan = _scope(QUESTIONS["study_vs_scores"])
    ds = services.invent_dataset("sess-cap", plan, 9999)  # capped to MAX_ROWS
    assert len(ds.rows) == services.MAX_ROWS


def test_refinement_flow_re_scopes():
    scope1, _ = services.scope_question(QUESTIONS["study_vs_scores"])
    refinement = "Does sleep mediate the effect of study time on exam scores?"
    scope2, mode = services.scope_question(QUESTIONS["study_vs_scores"], refinement)
    assert mode == "mock"
    assert scope2.dataset_name == "study_vs_scores"  # refinement still resolves to the template
    assert scope2.suggested_rows > 0


def _messy_csv() -> str:
    df = pd.DataFrame({
        "study_mode": ["group", "solo", "group", "solo", "group"],
        "weekly_hours": [3, 5, None, 8, 10],
        "quiz_score": [60, 70, 80, 90, 95],
    })
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return base64.b64encode(buf.getvalue().encode()).decode()


def test_augment_preserves_originals_and_tags_augmented():
    csv_b64 = _messy_csv()
    ds = services.augment_dataset("sess-aug", csv_b64, 20, "survey.csv")
    originals = [r for r in ds.rows if r.provenance == "original"]
    augmented = [r for r in ds.rows if r.provenance == "augmented"]
    assert len(originals) == 5
    assert len(augmented) == 15
    assert len(ds.rows) == 20
    assert ds.warning and "original" in ds.warning and "augmented" in ds.warning


def test_augment_completeness_improves():
    csv_b64 = _messy_csv()
    raw = pd.read_csv(io.StringIO(base64.b64decode(csv_b64).decode()))
    before = quality.completeness(raw)
    ds = services.augment_dataset("sess-aug2", csv_b64, 15, "survey.csv")
    after_df = pd.DataFrame([r.values for r in ds.rows])
    after = quality.completeness(after_df)
    assert after > before


def test_augment_baseline_audit_saved():
    csv_b64 = _messy_csv()
    ds = services.augment_dataset("sess-aug3", csv_b64, 12, "survey.csv")
    baseline = Storage().load_baseline_audit(ds.dataset_id)
    assert baseline is not None
    assert "duplicate_rate" in baseline and "diversity" in baseline


def test_augment_error_paths():
    with pytest.raises(services.ServiceError):
        services.augment_dataset("s", "not-base64!!!", 10, None)
    with pytest.raises(services.ServiceError):
        services.augment_dataset("s", _messy_csv(), 0, None)
    # empty CSV → error
    empty = base64.b64encode(b"").decode()
    with pytest.raises(services.ServiceError):
        services.augment_dataset("s", empty, 10, None)


def test_augment_no_op_when_target_smaller():
    csv_b64 = _messy_csv()
    ds = services.augment_dataset("sess-noop", csv_b64, 3, "survey.csv")
    assert all(r.provenance == "original" for r in ds.rows)
