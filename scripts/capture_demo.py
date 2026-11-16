"""
5.4 / 5.6 / 5.7 — scripted user walkthrough (team-member run), captures:
  - per-screen timing (usability session data, 5.4)
  - demo video: assets/demo_video.webm (Playwright records the whole run)
  - screenshots: assets/screenshots/*.png

Runs the template-only, zero-key flow: Ask → Build → Audit → Receipt → Export.

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
        pause(1.5)
        page.click("text=Study vs. scores")
        page.wait_for_selector("#plan-card", state="visible", timeout=15000)
        # simulate a student edit (contributes to the F11 log)
        page.fill("#plan-plan", "Generate synthetic student records with study hours, prior GPA, sleep hours, and exam score; score band as target.")
        pause(2.0)
        mark("Ask: template picked + plan shown")
        page.screenshot(path=str(SHOTS / "01_ask_plan.png"), full_page=True)

        # ---------- Screen 2: Build ----------
        page.click("#btn-goto-build")
        page.wait_for_selector("#screen-build:not([hidden])")
        pause(1.5)
        page.click("#btn-invent")
        page.wait_for_selector("#dataset-panel:not([hidden])", timeout=30000)
        page.wait_for_function(
            "document.querySelector('#ds-counts').textContent.includes('synthetic')", timeout=10000)
        pause(2.0)
        mark("Build: dataset invented + preview shown")
        page.screenshot(path=str(SHOTS / "02_build_invent.png"), full_page=True)

        # ---------- Screen 3: Audit ----------
        page.click("#btn-goto-audit")
        page.wait_for_selector("#audit-grid .metric-card", timeout=30000)
        pause(2.5)  # hero shot: before/after charts
        mark("Audit: before/after charts rendered")
        page.screenshot(path=str(SHOTS / "03_audit_before_after.png"), full_page=True)

        # ---------- Screen 4: Receipt ----------
        page.click("#btn-goto-receipt")
        page.wait_for_selector("#receipt-card .receipt-section", timeout=30000)
        pause(2.0)
        mark("Receipt: fields + contribution log rendered")
        page.screenshot(path=str(SHOTS / "04_receipt.png"), full_page=True)
        # variant switch (F8)
        page.select_option("#variant-select", "teacher-check")
        page.wait_for_selector("#receipt-card .receipt-section", timeout=10000)
        pause(1.5)
        mark("Receipt: teacher-check variant rendered")
        page.screenshot(path=str(SHOTS / "05_receipt_teacher_check.png"), full_page=True)

        # ---------- Screen 5: Export ----------
        page.click("#btn-goto-export")
        page.wait_for_selector("#export-files .file-card", timeout=30000)
        page.wait_for_selector("#closing-card:not([hidden])", timeout=10000)
        pause(2.0)
        mark("Export: package + summary rendered")
        page.screenshot(path=str(SHOTS / "06_export.png"), full_page=True)

        # ---------- screenshot for augment path (bonus, uses sample CSV) ----------
        page.click(".step[data-route='build']")
        page.wait_for_selector("#screen-build:not([hidden])")
        page.click("text=Augment a CSV")
        pause(1.2)
        page.set_input_files("#augment-file", str(ROOT / "data/samples/messy_study_survey.csv"))
        page.click("#btn-augment")
        page.wait_for_selector("#dataset-panel:not([hidden])", timeout=30000)
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
