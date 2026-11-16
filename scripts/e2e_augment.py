"""
5.2 — E2E test, augment path: messy demo CSVs → augment → audit before/after.

Creates/uses the 2 messy CSVs in data/samples/, augments them, and asserts
the before/after audit shows real improvement (missing values filled,
duplicates removed) and that the 3 export files download.

Usage:  python3 scripts/e2e_augment.py [--base http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

import httpx

SAMPLES = [
    "data/samples/messy_study_survey.csv",
    "data/samples/messy_plant_survey.csv",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    root = Path(__file__).resolve().parents[1]

    ok = True
    for i, rel in enumerate(SAMPLES, 1):
        path = root / rel
        csv_b64 = base64.b64encode(path.read_bytes()).decode()
        sid = f"e2e-aug-{i}"
        print(f"\n[{i}/2] sample: {rel} ({path.stat().st_size} bytes)")
        try:
            r = httpx.post(f"{base}/api/datasets/augment", json={
                "session_id": sid, "csv": csv_b64, "target_rows": 20,
                "filename": path.name,
            })
            assert r.status_code == 200, r.text
            ds = r.json()
            tags = [row["provenance"] for row in ds["rows"]]
            n_orig = tags.count("original")
            n_aug = tags.count("augmented")
            assert n_orig == 5, f"expected 5 originals (1 dup removed), got {n_orig}"
            assert n_aug == 15
            print(f"  augment  OK  rows={len(ds['rows'])} original={n_orig} augmented={n_aug}")

            # before/after audit
            r = httpx.get(f"{base}/api/datasets/{ds['dataset_id']}/audit")
            assert r.status_code == 200, r.text
            audit = r.json()
            comp = audit["metrics"]["completeness"]
            dup = audit["metrics"]["duplicate_rate"]
            assert comp["after"] > comp["before"], "completeness must improve"
            assert dup["before"] > 0, "baseline must contain the duplicate row"
            assert dup["after"] == 0, "cleaned set must be duplicate-free"
            print(f"  audit    OK  completeness {comp['before']:.3f} -> {comp['after']:.3f} | duplicates {dup['before']:.3f} -> {dup['after']:.3f}")

            # downloads
            r = httpx.get(f"{base}/api/exports/{sid}")
            assert r.status_code == 200, r.text
            bundle = r.json()
            for name, url in bundle["files"].items():
                fr = httpx.get(f"{base}{url}")
                assert fr.status_code == 200 and fr.content, name
            csv = httpx.get(f"{base}{bundle['files']['dataset.csv']}").text
            assert "provenance" in csv.splitlines()[0]
            print(f"  export   OK  3 files download; CSV provenance header present")
            print(f"  => sample {rel}: PASS")
        except AssertionError as e:
            ok = False
            print(f"  => sample {rel}: FAIL — {e}")

    print("\nE2E augment path:", "ALL SAMPLES PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
