"""
quality.py — ResearchLoop quality/audit engine.

Real, computed quality metrics for student datasets (F4). No hardcoded
values: every number is calculated from the data. Used by both the app
and the pre-flight smoke test.

Metrics:
  - duplicate_rate   : exact duplicates (fraction of rows)
  - near_duplicate_rate : rows with embedding cosine > 0.95 to an earlier row
  - diversity        : mean pairwise cosine similarity (lower = more diverse)
  - completeness     : mean non-null fraction across columns
  - label_coverage   : fraction of rows with a valid (non-null) label
  - distribution_sanity: numeric-column checks (constant columns, negative values)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

NEAR_DUPLICATE_THRESHOLD = 0.95


def _text_column(df: pd.DataFrame) -> pd.Series:
    """Collapse a DataFrame into a single text blob per row for TF-IDF comparison."""
    return df.apply(lambda row: " ".join(str(x) for x in row), axis=1)


def duplicate_rate(df: pd.DataFrame) -> float:
    """Fraction of rows that are exact duplicates of an earlier row."""
    if df.empty:
        return 0.0
    dup_mask = df.duplicated(keep="first")
    return float(dup_mask.mean())


def near_duplicate_rate(df: pd.DataFrame, threshold: float = NEAR_DUPLICATE_THRESHOLD) -> float:
    """Fraction of rows with cosine similarity > threshold to any earlier row."""
    if df.empty:
        return 0.0
    texts = _text_column(df)
    vectorizer = TfidfVectorizer(max_features=500, lowercase=True)
    try:
        mat = vectorizer.fit_transform(texts)
    except ValueError:
        return 0.0
    sims = cosine_similarity(mat)
    near = 0
    for i in range(len(df)):
        if np.any(sims[i, :i] > threshold):
            near += 1
    return float(near / len(df))


def diversity(df: pd.DataFrame) -> float:
    """Mean pairwise cosine similarity; lower means more diverse."""
    if len(df) < 2:
        return 0.0
    texts = _text_column(df)
    vectorizer = TfidfVectorizer(max_features=500, lowercase=True)
    try:
        mat = vectorizer.fit_transform(texts)
    except ValueError:
        return 0.0
    sims = cosine_similarity(mat)
    iu = np.triu_indices_from(sims, k=1)
    return float(sims[iu].mean())


def completeness(df: pd.DataFrame) -> float:
    """Mean fraction of non-null values across all columns."""
    if df.empty:
        return 0.0
    return float(df.notna().mean().mean())


def label_coverage(df: pd.DataFrame, label_col: str | None) -> float:
    """Fraction of rows with a valid (non-null) label, if a label column exists."""
    if label_col is None or label_col not in df.columns:
        return 1.0
    return float(df[label_col].notna().mean())


def distribution_sanity(df: pd.DataFrame, numeric_cols: list[str] | None = None) -> dict:
    """Check numeric columns for constant columns and negative values."""
    numeric_cols = numeric_cols or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    issues: list[str] = []
    for col in numeric_cols:
        if col not in df.columns:
            continue
        col_data = df[col].dropna()
        if col_data.empty:
            continue
        if col_data.nunique() <= 1:
            issues.append(f"column '{col}' is constant ({col_data.iloc[0]})")
        if (col_data < 0).any():
            issues.append(f"column '{col}' contains negative values")
    return {"passed": len(issues) == 0, "issues": issues}


def audit_dataset(df: pd.DataFrame, label_col: str | None = None) -> dict:
    """Full audit report for a dataset (F4)."""
    return {
        "duplicate_rate": duplicate_rate(df),
        "near_duplicate_rate": near_duplicate_rate(df),
        "diversity": diversity(df),
        "completeness": completeness(df),
        "label_coverage": label_coverage(df, label_col),
        "distribution_sanity": distribution_sanity(df),
    }


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    F3 cleaning step: drop exact duplicates, fill missing numeric values with the
    column median, strip whitespace on string columns. Returns cleaned df + stats.
    """
    before_n = len(df)
    cleaned = df.drop_duplicates(keep="first").copy()
    for col in cleaned.columns:
        if pd.api.types.is_numeric_dtype(cleaned[col]):
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())
        elif pd.api.types.is_object_dtype(cleaned[col]):
            cleaned[col] = cleaned[col].astype(str).str.strip()
    stats = {"rows_before": before_n, "rows_after": len(cleaned), "rows_removed": before_n - len(cleaned)}
    return cleaned, stats
