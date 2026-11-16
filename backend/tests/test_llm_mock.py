"""1.4 — MockLLM: deterministic, offline, template-driven, mode-labeled."""

import pandas as pd

from app.llm import MockLLM
from app.schemas import ScopeResult

QUESTIONS = {
    "study_vs_scores": "Does study time affect exam scores?",
    "plant_heat_tolerance": "Which local plant species tolerates heat best?",
    "group_study": "Do students who study in groups score higher?",
}


def test_scope_matches_templates():
    llm = MockLLM()
    for template_id, question in QUESTIONS.items():
        scope, mode = llm.scope(question)
        assert scope.dataset_name == template_id, f"{template_id} not matched"
        assert mode == "mock"
        assert scope.suggested_rows > 0
        assert len(scope.variables) > 0
        assert scope.refinements, "templates should provide refinements (F7)"


def test_scope_free_question_falls_back_gracefully():
    llm = MockLLM()
    scope, mode = llm.scope("whatever about anything at all")
    assert mode == "mock"
    assert scope.research_type == "descriptive"
    assert scope.suggested_rows == 50


def test_mock_is_deterministic():
    llm = MockLLM()
    s1, _ = llm.scope(QUESTIONS["study_vs_scores"])
    s2, _ = llm.scope(QUESTIONS["study_vs_scores"])
    assert s1 == s2
    rows1, _ = llm.invent(s1, 30)
    rows2, _ = llm.invent(s1, 30)
    assert rows1 == rows2


def test_invent_row_count_and_provenance():
    llm = MockLLM()
    scope, _ = llm.scope(QUESTIONS["study_vs_scores"])
    rows, mode = llm.invent(scope, 80)
    assert len(rows) == 80
    assert mode == "mock"
    assert all(r.provenance == "synthetic" for r in rows)


def test_invent_values_respect_template_ranges():
    llm = MockLLM()
    scope, _ = llm.scope(QUESTIONS["study_vs_scores"])
    rows, _ = llm.invent(scope, 100)
    hours = [r.values["study_hours"] for r in rows]
    scores = [r.values["exam_score"] for r in rows]
    assert all(2 <= h <= 20 for h in hours), "study_hours outside template range"
    assert all(40 <= s <= 100 for s in scores), "exam_score outside template range"


def test_augment_tags_original_and_augmented():
    llm = MockLLM()
    df = pd.DataFrame({
        "study_mode": ["group", "solo", "group", "solo"],
        "quiz_score": [60, 70, 80, 90],
    })
    out, mode = llm.augment(df, 12)
    assert mode == "mock"
    assert len(out) == 12
    assert (out["provenance"] == "original").sum() == 4
    assert (out["provenance"] == "augmented").sum() == 8
    assert (out["quiz_score"].notna()).all()


def test_methodology_is_honest():
    llm = MockLLM()
    scope, _ = llm.scope(QUESTIONS["group_study"])
    text, mode = llm.draft_methodology(scope, 90, "the dataset is synthetic.")
    assert mode == "mock"
    assert "mock mode" in text
    assert "no external sources were consulted" in text
