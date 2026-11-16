# ResearchLoop — Master Plan

**Project:** ResearchLoop (ML Empowerment Build Challenge 4.0)
**Deadline:** Dec 1, 2026, 9:00 PM PT (submit buffer day) · **Winners:** Dec 10
**Sponsors:** Adaption Labs · Rise Research · **Organizer:** ML Empowerment Foundation
**Stack:** FastAPI + pandas/scikit-learn + OpenAI-compatible LLM (MockLLM fallback) + Adaption adapter + Next.js or static SPA frontend

---

## 1. How to use this folder

Every phase file (`phase_0.md` … `phase_6.md`) is self-contained and structured the same way:

| Section | What it contains |
|---|---|
| **Goals** | What the phase must achieve |
| **Requirements / prerequisites** | What must exist before starting |
| **Sub-phases & tasks** | Task table: ID, task, description, acceptance, **status** |
| **Feature behavior** | How the features built in this phase work (the "how it works" map) |
| **Testing** | Unit / integration test plan and criteria |
| **Validation** | Definition of Done checklist for the phase |
| **Results** | Evidence & outputs recorded as work completes |
| **Tracking notes** | Progress, blockers, decisions |

**Status convention:** `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked (note blocker)

**Update rule:** after any work session, update the status in the relevant task row and the **Progress dashboard** below. Do not delete history — append results.

## 2. Phase overview

| Phase | Name | Days (planned) | Status | Delivers |
|---|---|---|---|---|
| **0** | Foundation & Pre-Flight | done (pre-coding) | ✅ Complete | Workspace, docs, stack, contracts, quality engine verified, templates, git |
| **1** | Backend Foundation | 1–2 | ✅ Complete | Schemas, config, LLM layer, Adaption adapter, dataset storage |
| **2** | Core Data Features | 3–5 | ✅ Complete | F1 Scope · F2 Invent · F3 Augment · F7 refinement flow |
| **3** | Audit, Receipt & Export | 6–8 | ✅ Complete | F4 Audit · F5 Receipt · F6 Export · F8 variants · F9 source honesty · F11 contribution log |
| **4** | Frontend | 8–11 | ✅ Complete | 5 screens: Ask → Build → Audit → Receipt → Export (static SPA, no build step) |
| **5** | Integration, Testing & Demo Assets | 11–14 | ✅ Complete | E2E (mock+augment), spot-check, usability run, demo video, 7 screenshots, receipt sample |
| **6** | Submission & Final Validation | 14–16 | 🔲 Not started | Devpost submission, final checks, submit by Dec 1 |

## 3. Feature → phase mapping (the tracking matrix)

| Feature | What it is | Phase | Status |
|---|---|---|---|
| **F1** Question → Scope | Parse rough question into research plan | 2 | ✅ |
| **F2** Dataset Invention | Generate synthetic dataset for a plan | 2 | ✅ |
| **F3** Dataset Augmentation | Clean + augment uploaded small CSV | 2 | ✅ |
| **F4** Quality Audit (before/after) | Real metrics + dashboard data | 3 | ✅ |
| **F5** Disclosure Receipt | C2PA-style AI-use receipt | 3 | ✅ |
| **F6** Research-Ready Export | Dataset + receipt + methodology bundle | 3 | ✅ |
| **F7** Guided Refinement | Suggest better research questions | 2 (partial) / 4 | ✅ (API flow) |
| **F8** Receipt Variants | standard / journal-style / teacher-check | 3 | ✅ |
| **F9** Source Grounding | Real sources in receipt only if consulted | 3 | ✅ (no fabrication, test-enforced) |
| **F10** Scenario Templates | 3 demo templates | 0 (data) / 4 (UI) | ✅ data done |
| **F11** Student Contribution Log | Log of student edits on receipt | 3 | ✅ |
| **F12** Plain-language Explainers | Tooltips on metrics/receipt | 4 | 🔲 |
| **N1–N4** stretch | multilingual / mentor mode / re-runs / gallery | — | ⛔ excluded unless core done |

## 4. Timeline (16 days → phases)

| Day | Phase work |
|---|---|
| 0 (done) | Phase 0 — pre-coding complete |
| 1–2 | Phase 1 — backend foundation |
| 3–5 | Phase 2 — F1/F2/F3 (MockLLM first; real LLM when key available) |
| 6–7 | Phase 3 — F4 audit endpoint + dashboard data |
| 8 | Phase 3 — F5/F6 receipt + export; **Phase 4 starts** |
| 9 | Phase 4 — frontend screens (demo spine) |
| 10–11 | Phase 4 — audit chart, receipt screen, export screen |
| 11–13 | Phase 5 — E2E, student testing, screenshots, video |
| 14 | Phase 6 — Devpost description, README, final validation |
| 15 | Phase 6 — buffer: fix anything, re-record video if needed |
| 16 (Dec 1) | **Phase 6 — SUBMIT** (deadline Dec 2, 2:45 AM EST) |

## 5. Dependencies (what blocks what)

```
Phase 0 (done) ──► Phase 1 (schemas, LLM, adapter) ──► Phase 2 (F1/F2/F3)
                                              │
Phase 1 ──► Phase 3 (audit uses quality engine; receipt uses schemas)
                                              │
Phase 2 + 3 ──► Phase 4 (frontend consumes backend API)
                                              │
Phase 4 ──► Phase 5 (E2E only works when frontend + backend talk)
                                              │
Phase 5 ──► Phase 6 (assets + submission)
```

- **Hard gate:** Phase 4 cannot start before Phase 1 exists (frontend needs the API contract; the contract itself is already defined in `docs/05`).
- **Demo-safety gate:** the app must run end-to-end in MockLLM mode before any real API keys are used (Phase 5 acceptance).

## 6. Global risks (carried from docs/03)

| Risk | Mitigation |
|---|---|
| LLM API unavailable | MockLLM keeps every feature working offline, labeled |
| Adaption API unavailable | `ADAPTION_MODE=emulated`, disclosed in receipt + Devpost text |
| Feature scope creep | Hard rule: F1–F6 only; F7–F12 only if core is solid |
| Demo breaks during recording | Templates (F10) + MockLLM + recorded buffer day (day 15) |
| Real-student testing unavailable | Use team members; template-driven scripted flow as fallback |

## 7. Project-level Definition of Done

- [ ] All core features F1–F6 implemented, tested, and documented
- [ ] App runs end-to-end in **both** mock mode and real mode (if keys available)
- [ ] Quality metrics are real (verified by manual spot-check)
- [ ] Every synthetic/augmented row tagged; receipts accurate (honesty gates from `docs/06`)
- [ ] 5-screen demo flow works offline (MockLLM) — recorded in demo video
- [ ] Demo video (90–120s) + 3+ screenshots in `assets/`
- [ ] README with setup + run instructions
- [ ] Devpost submission complete: title, description to rubric, files, repo link, team details
- [ ] **Submitted by Dec 1** (buffer day before deadline)

## 8. Progress dashboard

| Phase | Status | % done | Notes |
|---|---|---|---|
| 0 — Foundation & Pre-Flight | ✅ Complete | 100% | Quality engine 6/6 tests pass; **validation pass executed** (templates 3/3, engine imports, live demo green) |
| 1 — Backend Foundation | ✅ Complete | 100% | schemas, config, LLM layer (real+Mock), Adaption adapter, storage; 32/32 tests; app boots with zero keys |
| 2 — Core Data Features | ✅ Complete | 100% | F1/F2/F3 + F7 flow on backend; scope/invent/augment endpoints; diversity retry ≤5%; originals+augmented tagging; 53/53 tests (1 real-mode skip) |
| 3 — Audit, Receipt & Export | ✅ Complete | 100% | F4 before/after audit + interpretations; F5 receipt with SHA-256 hash, mode-accurate tools, no fabricated sources; F6 export bundle (CSV+receipt+methodology); F8 variants; F11 contribution log; 70/71 tests |
| 4 — Frontend | ✅ Complete | 100% | 5-screen static SPA (vanilla HTML/CSS/JS, served by FastAPI); template picker + editable plan; invent/augment previews; SVG before/after charts; receipt with variants + mode badge; export downloads; F12 tooltips; demo script; 73/74 tests |
| 5 — Integration & Demo Assets | ✅ Complete | 100% | E2E mock (3 templates) + augment (2 messy CSVs) pass; metrics spot-check matches hand-calc; team-member usability run (~17s flow, quote captured); demo video + 7 screenshots + receipt sample in assets/; 3 bugs fixed; 73/74 tests |
| 6 — Submission & Final Validation | 🔲 Not started | 0% | — |

**Overall: 6/7 phases complete (~86%) — Phases 0–5 validated**
