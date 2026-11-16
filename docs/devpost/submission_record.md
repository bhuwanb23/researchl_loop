# Phase 6 — Submission Record (6.12)

**Submission status:** ✅ **PACKAGE READY — awaiting team execution on Devpost**
**Prepared:** 2026-11-16 (Asia/Calcutta) · **Hard deadline:** Dec 1, 9:00 PM PT (submit Dec 1, not Dec 2)

The submission *content* is complete and validated. The actual Devpost form submission requires
the team's Devpost account/registration (a user action per docs/06 §A #8) — it cannot be
executed from the workspace. The exact, ready-to-paste package is `docs/devpost/submission.md`.

## Submit — step by step

1. **Register/log in** on the ML Build Challenge 4.0 Devpost page; claim the $1000 Adaption
   credits via the referral link (docs/06 §A #8).
2. **Create the submission** with the content from `docs/devpost/submission.md`, in this order:
   - **Title** → 6.1 title + tagline.
   - **Description** → paste 6.2 (Problem), 6.3 (Solution), 6.4 (Key Features), 6.5
     (Technologies Used), 6.6 (Target Users), 6.7 (Social Impact) — all six parts.
   - **Files** → upload: `assets/demo_video.webm`, the 7 screenshots
     (`assets/screenshots/`), `assets/receipt_sample.json`.
   - **Link** → the pushed repo URL (replace the `your-org` placeholder in 6.8).
   - **Team details** → fill the member table (6.9) with real student names/roles.
3. **Re-read the honesty audit** at the bottom of `submission.md` before finalizing:
   no unbuilt features, sponsor usage = Adaption *emulated*, LLM = *mock*.
4. **Submit** — then **screenshot the confirmation** and save it here:
   `assets/submission_confirmation.png`.
5. **Update this record** with the submission timestamp:

```
Submitted at: <YYYY-MM-DD HH:MM TZ>
Confirmation screenshot: assets/submission_confirmation.png
```

## Buffer-day plan (6.12)

- If anything is flagged after a first submission pass: fix in repo, re-run
  `scripts/e2e_mock.py` + `scripts/e2e_augment.py`, re-capture `scripts/capture_demo.py`, and
  re-submit (never an incomplete description — prioritize 6.2–6.5 + 6.8 if time runs short).
- Winners are announced Dec 10 — keep the repo tidy until then.

## Notes

- **Mock-only baseline, stated precisely:** the demo runs in labeled mock LLM + emulated
  Adaption mode. Real LLM/Adaption integrations are implemented and documented in the repo;
  they activate with credentials. This is stated in the submission (6.5, 6.7) — never imply
  otherwise.
- **Impact evidence is honest:** usability evidence is a team-member run (external students
  unavailable), noted in 6.7.
