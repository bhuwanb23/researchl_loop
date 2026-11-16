"""
Pre-flight smoke test for the quality engine (04/06 docs: verify before app code).

Run:  cd backend && python -m venv .venv && source .venv/bin/activate
      pip install -r requirements.txt && pytest tests/ -v
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.quality import (
    audit_dataset,
    clean_dataset,
    completeness,
    diversity,
    duplicate_rate,
    label_coverage,
)


def _messy_dataset() -> pd.DataFrame:
    """A small realistic messy dataset: duplicates, missing values, a constant col."""
    rows = []
    for i in range(40):
        mode = "group" if i % 2 == 0 else "solo"
        rows.append(
            {
                "study_mode": mode,
                "weekly_hours": 3 + (i % 10),
                "quiz_score": 50 + (i % 40),
                "satisfaction": 2 + (i % 4),
            }
        )
    df = pd.DataFrame(rows)
    # inject missing values first, so duplicated rows stay intact
    df.loc[0, "quiz_score"] = None
    df.loc[1, "weekly_hours"] = None
    # inject 4 exact duplicates of intact rows (4-7)
    df = pd.concat([df, df.iloc[4:8]], ignore_index=True)
    # constant column for sanity check
    df["constant_col"] = 7
    return df


def test_duplicate_rate_detects_injected_duplicates():
    df = _messy_dataset()
    rate = duplicate_rate(df)
    # 44 rows, 4 duplicates -> ~9%
    assert 0.05 < rate < 0.15, f"unexpected duplicate rate: {rate}"


def test_diversity_and_completeness_are_real_numbers():
    df = _messy_dataset()
    assert 0.0 <= diversity(df) <= 1.0
    assert 0.0 < completeness(df) < 1.0, "completeness should be < 1.0 due to missing values"


def test_label_coverage():
    df = _messy_dataset()
    assert 0.0 < label_coverage(df, "quiz_score") < 1.0
    assert label_coverage(df, None) == 1.0


def test_audit_dataset_structure():
    df = _messy_dataset()
    report = audit_dataset(df, label_col="quiz_score")
    assert set(report.keys()) == {
        "duplicate_rate",
        "near_duplicate_rate",
        "diversity",
        "completeness",
        "label_coverage",
        "distribution_sanity",
    }
    assert report["distribution_sanity"]["passed"] is False  # constant col detected


def test_clean_dataset_removes_duplicates_and_fills_missing():
    df = _messy_dataset()
    cleaned, stats = clean_dataset(df)
    assert stats["rows_after"] == stats["rows_before"] - 4
    assert cleaned["quiz_score"].isna().sum() == 0
    assert cleaned["weekly_hours"].isna().sum() == 0
    # completeness should improve after cleaning
    assert completeness(cleaned) > completeness(df)


def test_cleaned_dataset_passes_distribution_sanity():
    df = _messy_dataset().drop(columns=["constant_col"])
    cleaned, _ = clean_dataset(df)
    report = audit_dataset(cleaned)
    assert report["distribution_sanity"]["passed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
