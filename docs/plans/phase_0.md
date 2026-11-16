# Phase 0 — Foundation & Pre-Flight

**Status:** ✅ COMPLETE · **Planned days:** pre-coding · **Features delivered:** none directly (enables all) · **Blocks:** all phases

---

## Goals
- Organize the workspace into a single, trackable project structure
- Complete all planning before any application code
- Verify the technical stack actually works (dependencies install, quality engine computes real metrics)
- Define contracts (API + data) that every later phase builds against

## Requirements / prerequisites
- Sandbox with Python 3.13 + Node 20 (verified)
- No external API keys required (mock mode is the baseline)

## Sub-phases & tasks

| ID | Task | Description | Acceptance | Status |
|---|---|---|---|---|
| 0.1 | Workspace reorganization | Create `researchloop/` with docs/, backend/, frontend/, data/, scripts/, assets/; move the 3 research docs into `docs/` | Clean tree, no stray root files | [x] |
| 0.2 | Challenge research doc | Challenge facts, timeline, judging, sponsors | Verified live (deadline re-checked Nov 16) | [x] |
| 0.3 | Literature review | Primary + secondary sources, gap analysis, novelty statement | Primary sources across 8 clusters; white space identified | [x] |
| 0.4 | Ideation doc | Precise concept, feature taxonomy (core/important/leveraged/stretch/excluded) | F1–F6 core scope locked; exclusions justified | [x] |
| 0.5 | Tech stack decision | Chosen stack + rejected alternatives + non-negotiable rules | `docs/04` | [x] |
| 0.6 | Architecture & API contract | Repo layout, runtime diagram, 6 endpoints with JSON contracts, schemas | `docs/05` — every later phase codes against this | [x] |
| 0.7 | Preflight & acceptance doc | Checklist, per-feature DoD, demo acceptance, honesty gates | `docs/06` | [x] |
| 0.8 | Quality engine (`backend/app/quality.py`) | Real metrics: duplicate rate, near-dup, diversity, completeness, label coverage, distribution sanity + clean step | Module importable, all functions work on real frames | [x] |
| 0.9 | Quality engine smoke tests | 6 pytest cases on a deliberately messy dataset | **6/6 PASS** (1.30s) | [x] |
| 0.10 | Demo templates | 3 JSON templates: study_vs_scores, plant_heat_tolerance, group_study | Match scope contract in `docs/05` | [x] |
| 0.11 | Repo hygiene | `.gitignore`, `.env.example`, `requirements.txt`, README, git init | 3 commits, secrets excluded | [x] |

## Feature behavior (what this phase establishes)
- **The quality engine** is the only "real" computation that every other phase leans on: it computes metrics from actual data (no hardcoded values). F4's dashboard will display these numbers; F3's augmentation will use its clean step.
- **The API contract** (docs/05) defines how frontend and backend talk — frontend phases code against the documented JSON, not against the backend's internals.

## Testing
- `pytest backend/tests/` — 6/6 pass. Tests cover: duplicate detection, diversity bounds, label coverage, audit structure, clean-and-fill, post-clean sanity.

## Validation (DoD)
- [x] Workspace organized, no stray files
- [x] All planning docs exist and are consistent with each other
- [x] Stack installs cleanly in venv
- [x] Quality engine verified with real data
- [x] Deadline re-verified live (Dec 1, 9:00 PM PT)

## Results
- Environment: Python 3.13.18, Node 20.20.2, pip 26.2.2
- Quality engine: 6/6 tests pass — metrics are real and verified
- Git: 4 commits (pre-coding setup, test fix, hygiene, master plan + phase docs)

## Phase 0 validation pass (executed — read → analyze → execute → test → validate)
- **Read:** all phase artifacts re-read (plan file, quality.py, templates, docs/04–06, git state).
- **Analyze — 3 findings:** (1) typo `NEARIS_THRESHOLD` → fixed to `NEAR_DUPLICATE_THRESHOLD`; (2) module docstring mentioned "outliers" which the code never checked → docstring corrected to match behavior; (3) **contract mismatch:** `docs/05` audit contract listed 5 metrics but the engine returns 6 — added `near_duplicate_rate` to the contract (engine is source of truth).
- **Execute:** created `scripts/validate_phase0.py` (template contract check + engine import check + live functional demo with assertions).
- **Test:** fresh pytest run (cache cleared) → **6/6 PASS (1.72s)**. Validation script → **PASS**.
- **Validate (live demo evidence):** synthetic study_vs_scores, 65 rows with 3 real duplicates + 2 missing values:
  - duplicate_rate 0.046 → 0.000 · near_duplicate_rate 0.046 → 0.000 · completeness 0.992 → 1.000 · label_coverage 0.985 → 1.000 · diversity 0.030 → 0.030 · distribution_sanity passed before & after.
  - Assertions confirm: metrics are computed from data (not hardcoded), and cleaning genuinely improves quality.

## Tracking notes
- Two issues found and fixed during initial smoke testing (test-data injection order; pandas text-collapse quirk) — engine itself was correct.
- Validation pass found 3 documentation/typo-level issues (all fixed); no engine logic changes were needed — engine was already correct.
- **Open items carried forward:** LLM API key + Adaption credentials (mock/emulated mode covers until provided).
- **Phase 0 verdict:** ✅ VALIDATED — all DoD checkboxes met, evidence recorded.
