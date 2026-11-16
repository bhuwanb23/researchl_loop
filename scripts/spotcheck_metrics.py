"""
5.5 — Metrics spot-check: prove the audit numbers are REAL.

Hand-computes 3 metrics on a tiny known dataset, then compares them to
quality.audit_dataset output. If the engine ever produced fake numbers,
this would fail.

Metrics checked (hand calculation):
  - duplicate_rate:    4 rows, 1 exact copy of an earlier row → 1/4 = 0.25
  - completeness:      12 cells, 1 missing → 11/12 ≈ 0.9167
  - label_coverage:    label column with 3 of 4 rows filled → 3/4 = 0.75

Usage:  python3 scripts/spotcheck_metrics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pandas as pd  # noqa: E402

from app.engine import quality  # noqa: E402


def main() -> int:
    df = pd.DataFrame({
        "a": [1, 2, 3, 1],        # row 4 duplicates row 1 exactly (all columns)
        "b": ["x", "y", "z", "x"],
        "label": [10, 20, None, 10],  # one missing label
    })

    report = quality.audit_dataset(df, label_col="label")

    expected = {
        "duplicate_rate": (1 / 4, "1 exact duplicate of 4 rows"),
        "completeness": (11 / 12, "1 missing cell of 12"),
        "label_coverage": (3 / 4, "1 missing label of 4"),
    }

    ok = True
    print("Metric spot-check (hand-computed vs engine):")
    for key, (exp, why) in expected.items():
        got = report[key]
        match = abs(got - exp) < 1e-9
        ok = ok and match
        print(f"  {key:<18} hand={exp:.4f}  engine={got:.4f}  {'MATCH' if match else 'MISMATCH'}  ({why})")

    # sanity distribution check: constant column detection
    const_df = pd.DataFrame({"x": [5, 5, 5], "y": [1, 2, 3]})
    sanity = quality.distribution_sanity(const_df)
    const_ok = not sanity["passed"] and any("constant" in i for i in sanity["issues"])
    print(f"  distribution_sanity constant-col detection  {'MATCH' if const_ok else 'MISMATCH'}")
    ok = ok and const_ok

    print("\nSpot-check:", "ALL METRICS MATCH HAND CALCULATION" if ok else "MISMATCHES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
