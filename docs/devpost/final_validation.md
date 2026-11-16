# Phase 6 — Final Validation Checklist (6.11)

**Date:** 2026-11-16 · **Status:** all executable checks pass; user-action items flagged honestly.

## docs/06 §A — Pre-flight

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Python 3.13 + pip | ✅ | 3.13.18 |
| 2 | Node 20 + npm | ✅ | v20.20.2 (used for JS syntax checks + Playwright capture) |
| 3 | Backend deps install cleanly | ✅ | `backend/requirements.txt`; venv verified |
| 4 | Quality engine smoke test | ✅ | `test_quality.py` passes |
| 5 | LLM API access | ⏳ **user to confirm** | No `LLM_API_KEY` in this environment → **mock mode is the verified baseline** (stated everywhere) |
| 6 | Adaption API access | ⏳ **user to confirm** | No credentials → **emulated mode used** (labeled in receipts + UI) |
| 7 | Demo templates | ✅ | 3 templates in `data/templates/` |
| 8 | Devpost registration + credits claim | ⏳ **user action** | Submission copy is ready; registration + credit claim is the team's action |
| 9 | Repo initialized | ✅ | 10 commits, clean tree |

## docs/06 §B — Per-feature acceptance

- [x] **F1 Scope** — vague question → valid editable plan; refinements offered (tested, live).
- [x] **F2 Invent** — validated dataset, ≥90% valid rows, all `synthetic`, warning shown (tested, E2E).
- [x] **F3 Augment** — messy CSV (10–200 rows) cleaned + augmented; originals preserved & tagged; malformed CSV → helpful 400 (tested, E2E).
- [x] **F4 Audit** — real before/after for all 5 metrics + sanity; interpretations; numbers match manual spot-check.
- [x] **F5 Receipt** — all contract fields, hash verifies, mode accurately reported (mock), JSON export works.
- [x] **F6 Export** — one-click download; dataset.csv + receipt.json + methodology.md open correctly.
- [x] **F7–F12** — F7 refinement, F8 variants, F9 source honesty, F11 contribution log delivered; templates give a guaranteed demo path.

## docs/06 §C — Demo acceptance

- [x] Template → scoped plan → invent → preview → audit **before/after hero shot** → receipt →
  export package — all captured in `assets/demo_video.webm` + 7 screenshots. Works offline (mock).

## docs/06 §D — Honesty gates (non-negotiable)

- [x] Every synthetic/augmented row carries provenance in data + UI (enforced in schemas, storage, UI badges).
- [x] Receipt states whether LLM/Adaption ran in real or mock mode — `llm-mock` / `adaption-emulated`, always.
- [x] No hardcoded quality metrics — all computed (spot-check script proves 3 metrics vs hand calculation).
- [x] No fabricated sources in receipts — `sources_consulted: []`, test-enforced.
- [x] Devpost description states exactly which sponsor features were genuinely used —
  Adaption adapter implemented, **emulated mode used**; RealLLM implemented, **mock mode used**; both stated as such.

## Master plan §7 — Project DoD

- [x] All core features F1–F6 implemented, tested, and documented.
- [x] App runs end-to-end in mock mode (real mode: implemented, activates with keys — keys unavailable here, documented).
- [x] Quality metrics are real (verified by manual spot-check).
- [x] Every synthetic/augmented row tagged; receipts accurate (honesty gates above).
- [x] 5-screen demo flow works offline (MockLLM) — recorded in demo video.
- [x] Demo video (assets/demo_video.webm) + 3+ screenshots (7) in `assets/`.
- [x] README with setup + run instructions (root `README.md` — mock + real mode).
- [x] Devpost submission content complete: title, description (all parts), files, links, team structure (`docs/devpost/submission.md`).
- [ ] Submitted by Dec 1 — **submission execution is the team's action on Devpost** (see `submission_record.md` for the exact steps; content is submission-ready).

## Automated evidence (run 2026-11-16)

- `pytest tests/ -q` → **73 passed, 1 skipped** (skip = real-mode test; no key).
- `scripts/e2e_mock.py` → **ALL 3 TEMPLATES PASS**.
- `scripts/e2e_augment.py` → **ALL SAMPLES PASS** (completeness 0.917→1.000; duplicates 0.167→0.000).
- `scripts/spotcheck_metrics.py` → **ALL METRICS MATCH HAND CALCULATION**.
- Assets verified present & non-empty: demo_video.webm (2.0 MB), receipt_sample.json,
  7 screenshots, README.md, docs/devpost/submission.md.
- Receipt honesty gates verified on the sample: sources empty · oversight `prompt_guided` · hash present.
- Submission-copy honesty grep: no real-mode claim without the "implemented, not claimed" qualifier.
