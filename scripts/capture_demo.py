"""
5.4 / 5.6 / 5.7 — scripted user walkthrough (team-member run), captures:
  - per-screen timing (usability session data, 5.4)
  - demo video: assets/demo_video.webm (Playwright records the whole run)
  - screenshots: assets/screenshots/*.png

Runs the template-only, zero-key flow: Ask → Build → Audit → Receipt → Export.
Updated for the redesigned UI (pipeline arc + organized frontend structure).

Usage:  python3 scripts/capture_demo.py [--base http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SHOTS = ASSETS / "screenshots"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    ASSETS.mkdir(exist_ok=True)
    SHOTS.mkdir(exist_ok=True)
    timings: dict[str, float] = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(ASSETS),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        t0 = time.perf_counter()

        def mark(name: str) -> None:
            timings[name] = round(time.perf_counter() - t0, 2)
            print(f"[{timings[name]:>6.2f}s] {name}")

        def pause(seconds: float) -> None:
            page.wait_for_timeout(seconds * 1000)

        # ---------- Screen 1: Ask ----------
        page.goto(base + "/", wait_until="networkidle")
        pause(1.2)
        # template chip fills the question and refines it
        page.click("[data-template='study_vs_scores']")
        page.wait_for_selector("[data-refinement]", state="visible", timeout=15000)
        # pick the first refinement option → moves to Build
        page.click("[data-refinement] >> nth=0")
        page.wait_for_selector("#btn-invent", timeout=15000)
        pause(2.0)
        mark("Ask: template picked + refinement shown")
        page.screenshot(path=str(SHOTS / "01_ask_plan.png"), full_page=True)

        # ---------- Screen 2: Build — invent ----------
        page.wait_for_selector("#btn-invent", timeout=15000)
        page.click("#btn-invent")
        page.wait_for_selector("#btn-to-audit", state="visible", timeout=30000)
        pause(1.8)
        mark("Build: dataset invented + preview shown")
        page.screenshot(path=str(SHOTS / "02_build_invent.png"), full_page=True)

        # ---------- Screen 3: Audit ----------
        page.click("#btn-to-audit")
        page.wait_for_selector(".metric-grid .metric", timeout=30000)
        pause(2.5)  # hero shot: before/after bars + donut
        mark("Audit: before/after charts rendered")
        page.screenshot(path=str(SHOTS / "03_audit_before_after.png"), full_page=True)

        # ---------- Screen 4: Receipt ----------
        page.click("#btn-receipt")
        page.wait_for_selector(".receipt-doc .receipt-seal", timeout=30000)
        pause(2.0)
        mark("Receipt: verified document rendered")
        page.screenshot(path=str(SHOTS / "04_receipt.png"), full_page=True)
        # variant selector (F8) — re-sign as teacher-check
        page.select_option("#variant-select", "teacher-check")
        page.wait_for_function(
            "document.querySelector('.receipt-title .badge')?.textContent.includes('teacher-check')",
            timeout=15000,
        )
        pause(1.5)
        mark("Receipt: teacher-check variant re-signed")
        page.screenshot(path=str(SHOTS / "05_receipt_variant.png"), full_page=True)

        # ---------- Screen 5: Export ----------
        page.click("#btn-export")
        page.wait_for_selector(".metric-grid, .screen-head", timeout=30000)
        page.wait_for_selector("#btn-all", timeout=30000)
        pause(2.0)
        mark("Export: package files rendered")
        page.screenshot(path=str(SHOTS / "06_export.png"), full_page=True)

        # ---------- bonus: augment path via sample chip ----------
        page.click(".pipe-node:has-text('Build')")
        page.wait_for_selector("[data-sample]", timeout=15000)
        page.click("[data-sample='messy_study_survey.csv']")
        page.wait_for_selector("#btn-to-audit-b", state="visible", timeout=30000)
        pause(1.5)
        page.screenshot(path=str(SHOTS / "07_build_augment.png"), full_page=True)
        mark("Build: augment path (messy CSV) rendered")

        context.close()  # finalizes the recorded video
        browser.close()

    # Playwright saves the video under a generated name; keep the latest as demo_video.webm
    videos = sorted(ASSETS.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if videos:
        latest = videos[-1]
        final = ASSETS / "demo_video.webm"
        if latest != final:
            final.write_bytes(latest.read_bytes())
            latest.unlink()
        video = final
    else:
        video = ASSETS / "demo_video.webm"
    timing_path = ASSETS / "demo_timings.json"
    timing_path.write_text(json.dumps(timings, indent=2))
    print("\nCaptured:")
    print("  video     :", video, "(size:", video.stat().st_size if video.exists() else "MISSING", "bytes)")
    for name in sorted(timings):
        print(f"  timing    : {name} -> {timings[name]}s")
    return 0 if video.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
