# Phase 2 — Core Data Features (F1 · F2 · F3)

**Status:** ✅ **Complete** · **Days:** 3–5 · **Features delivered:** F1 Scope, F2 Invention, F3 Augmentation (+ F7 refinement flow) · **Blocks:** Phase 3, Phase 4

---

## Goals
- Implement the three core data features end-to-end on the backend
- Every generated/augmented row is **provenance-tagged** (synthetic / original / augmented) — the honesty rule
- Flow must work in MockLLM mode (demo-safety), and with a real LLM key if available

## Requirements / prerequisites
- Phase 1 complete (schemas, LLM layer, Adaption adapter, storage)
- Quality engine available for F3's clean step (Phase 0)

## Sub-phases & tasks

| ID | Task | Description | Acceptance | Status |
|---|---|---|---|---|
| 2.1 | F1 — scope endpoint | `POST /api/scope`: parse question → research_type, variables, suggested_rows, data_plan, refinements (F7) | Matches contract; vague inputs still return a usable plan | [x] |
| 2.2 | F1 — scope service logic | Validation: research_type ∈ {classification, regression, descriptive, survey}; variables non-empty; plan text generated | Invalid plans rejected with clear error | [x] |
| 2.3 | F2 — invention endpoint | `POST /api/datasets/invent`: plan + rows → dataset via LLM/Adaption layer | Rows match schema; every row tagged `synthetic`; warning text returned | [x] |
| 2.4 | F2 — row validation | Type/range checks on generated rows (numeric within bounds, categorical in allowed set); drop + retry invalid rows | ≥90% of rows pass validation; failures logged | [x] |
| 2.5 | F2 — diversity prompting | Generate with diversity constraints (varied values, no copy-paste rows); dedup after generation | Near-duplicate rate ≤ 5% on generated sets | [x] |
| 2.6 | F3 — augmentation endpoint | `POST /api/datasets/augment`: base64 CSV → parse → clean (quality.clean_dataset) → augment to target_rows | Original rows preserved & tagged; augmented rows tagged; malformed CSV → helpful error | [x] |
| 2.7 | F3 — augmentation logic | Augment = LLM variation of original rows respecting distribution; cap at reasonable bounds | Augmented data stays within variable ranges; no invented labels | [x] |
| 2.8 | F7 — refinement flow | Refinements from scope step are selectable and re-run scope | Selecting a refinement re-scopes the question | [x] |
| 2.9 | Integration tests — mock mode | Full F1→F2 and F1→F3 flows with MockLLM on all 3 templates | All 3 templates produce valid datasets | [x] |
| 2.10 | Integration tests — real mode | If `LLM_API_KEY` set: same flows with real LLM; compare output validity | Real-mode test skips gracefully without key | [x] |

## Feature behavior (how the features work)

**F1 — Question → Scope.** The LLM (or MockLLM) receives the raw question and returns a structured plan: research type, variables with types/units, suggested row count, a data plan, and 2–3 refinement options. The plan is rendered as an editable card. The plan is what F2 consumes.

**F2 — Dataset Invention.** Given the plan, the LLM generates rows in strict JSON matching the schema (variables + labels). Each row carries `provenance: "synthetic"`. Post-generation: type/range validation, dedup, near-dup check. If Adaption is in real mode, the same call goes through the Adaption Adaptive Data "invent" workflow — the UI shows which mode ran. The response includes a mandatory warning: *"All rows are synthetic and must be labeled as such."*

**F3 — Dataset Augmentation.** CSV upload → parse → `quality.clean_dataset` (dedup, median fill, whitespace strip) → LLM augments to the target size by creating *variations* of original rows (not copies, not invented facts) → each row tagged `original` or `augmented`. The original dataset is kept as the baseline so F4 can show before/after.

**F7 — Refinement.** If the question is vague, scope returns alternative re-framings; picking one re-runs scope. This is the guardrail that keeps the demo on track.

## Testing
- **Unit:** schema validation on all endpoints; provenance tag presence; F2 row-validation rejects out-of-range; F3 handles missing-column CSVs.
- **Integration (mock):** 3 templates × {invent, augment} = 6 happy paths; error paths: empty question, malformed CSV, zero target rows.
- **Integration (real):** same matrix if key available; log outputs for the demo.

## Validation (DoD)
- [ ] F1 returns valid, editable plans for all 3 templates + free questions
- [ ] F2 output: schema-correct, ≥90% valid rows, all tagged synthetic, near-dup ≤ 5%
- [ ] F3 output: originals preserved, augmented tagged, missing values filled, completeness improves
- [ ] All flows work offline (mock) and with real key (if provided)
- [ ] Honesty rule visible in API responses (warnings + provenance)

## Results

**Implementation summary:**
- **2.1** — `POST /api/scope` + `services.scope_question`; empty-question rejected with 400.
- **2.2** — `services._validate_plan` enforces ≥1 variable, positive row count, non-empty names.
- **2.3** — `POST /api/datasets/invent`; `services._row_is_valid` validates numeric ranges (template bounds) + categorical allowed-values + type correctness.
- **2.4** — every generated row tagged `synthetic`; `Dataset.warning` carries the honesty label + validation stats.
- **2.5** — F2 diversity loop: generation → per-row validation → drop invalid → exact dedup → **TF-IDF near-dup check**; retry with `offset` (changes value patterns via `MockLLM`/`RealLLM`) until valid ratio ≥90% **and** near-dup ≤5%; raises `ServiceError` if all 3 attempts fail (no fake diversity).
- **2.6** — `POST /api/datasets/augment`: CSV base64 → baseline audit (saved as `baseline_audit.json`) → `quality.clean_dataset` → LLM variation via `AdaptionClient.improve` → provenance re-tagging.
- **2.7** — originals preserved + tagged `original`; augmented rows tagged `augmented`; warning states the distinction; defensive provenance restore if LLM drops tags; numeric NaN filled post-augmentation.
- **2.8** — refinement flow: `/api/scope` with `refinement` re-scopes while resolving to the template; free questions fall back to descriptive.
- **2.9/2.10** — `tests/test_services.py` (14 tests) + `tests/test_api.py` (10 tests); real-mode test skips gracefully without `LLM_API_KEY`.

**Validation evidence:**
- `pytest tests/ -q` → **53 passed, 1 skipped** (the skip is the real-mode test, conditional on `LLM_API_KEY` — **mock mode used** for all validation).
- Live runtime (uvicorn, zero API keys):
  - `/api/health` → `{"status":"ok","llm_mode":"mock","adaption_mode":"emulated"}`
  - Scope: 3 templates resolved correctly (regression / descriptive / survey, 4 vars each) + free question → descriptive, 1 var, 50 rows.
  - Invent: 80/80 rows kept, 0 dropped, near-dup within limit, all `synthetic`, warning carried.
  - Augment: 4 originals preserved + 8 augmented tagged, warning states originals vs augmented.
  - Error paths: empty scope → 400; bad base64 → 400; target_rows=0 → 400.
- DoD checklist:
  - [x] F1 returns valid plans for all 3 templates + free questions (regression / descriptive / survey / descriptive fallback).
  - [x] F2 output: schema-correct, ≥90% valid rows, all tagged synthetic, near-dup ≤ 5% enforced with retry loop.
  - [x] F3 output: originals preserved, augmented tagged, missing values filled, completeness improves.
  - [x] Honesty rule visible in API responses (warnings + provenance).
  - [ ] All flows work offline (mock) ✅ **and with real key** — real-mode test **not run** (no `LLM_API_KEY` in this environment); it activates automatically when a key is present. **Mock/emulated mode is the verified baseline; submission must state this.**

## Tracking notes
- **Decision point:** real vs mock for demo — plan is mock-first; real mode tested if key is provided, but submission must state exactly which was used.
- **Risk:** F2 "looks fake" — mitigated by templates + diversity prompting + validation; the demo uses templates, so this is controlled.
