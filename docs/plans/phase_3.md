# Phase 3 — Audit, Receipt & Export (F4 · F5 · F6)

**Status:** ✅ **Complete** · **Days:** 6–8 · **Features delivered:** F4 Audit, F5 Receipt, F6 Export, F8 variants, F9 source honesty, F11 contribution log · **Blocks:** Phase 4 (receipt/export screens), Phase 5

---

## Goals
- Wire the verified quality engine into a live audit endpoint (F4)
- Build the disclosure receipt (F5) — the novelty artifact — with accurate mode reporting
- Package everything into a research-ready export (F6)
- Include the student contribution log (F11) and, if time allows, receipt variants (F8) and source grounding (F9)

## Requirements / prerequisites
- Phase 1 (schemas, receipt fields, storage) + Phase 2 (datasets exist with provenance)
- Quality engine from Phase 0 (already tested)

## Sub-phases & tasks

| ID | Task | Description | Acceptance | Status |
|---|---|---|---|---|
| 3.1 | F4 — audit endpoint | `GET /api/datasets/{id}/audit` → full metric report (duplicate, near-dup, diversity, completeness, label coverage, distribution sanity) | Report matches contract; numbers equal a manual spot-check | [x] |
| 3.2 | F4 — before/after pairing | Audit accepts a baseline dataset (pre-clean/pre-augment) and returns before/after per metric | Both sides computed; interpretation lines generated | [x] |
| 3.3 | F4 — interpretations | One-line plain-language meaning per metric + overall verdict | Each metric has an interpretive sentence | [x] |
| 3.4 | F5 — receipt builder | `POST /api/receipts`: builds receipt from dataset + session: question, source, AI tools + purpose, generated-vs-student split, human_oversight_level, sources, timestamp, integrity hash | All contract fields populated; hash valid; mode (real/mock/emulated) recorded | [x] |
| 3.5 | F5 — integrity hash | SHA-256 over receipt content (canonical JSON) | Hash verifies on reload | [x] |
| 3.6 | F11 — contribution log | Session records student edits (plan edits, row corrections, refinement picks); receipt lists them | Receipt shows counts/actions of student work | [x] |
| 3.7 | F8 — receipt variants | `standard` / `journal-style` (COPE/Nature fields) / `teacher-check` (one-page) — at least standard + one variant | Variant selection changes receipt layout | [x] |
| 3.8 | F9 — source grounding | Receipt sources = only URLs/refs genuinely consulted during the run (mock: none, stated as such) | **No fabricated sources** — verified by test | [x] |
| 3.9 | F6 — export bundle | `GET /api/exports/{session_id}` → dataset.csv + receipt.json + methodology.md (auto-drafted, editable) as downloadable files | All three files open correctly; CSV keeps provenance column | [x] |
| 3.10 | Methodology draft | LLM drafts a short methodology paragraph from the plan + dataset; student-editable | Draft is accurate to the plan; never overclaims | [x] |
| 3.11 | Tests — audit & receipt | Metrics correctness (manual check), receipt field completeness, hash verification, no-fabricated-sources test, export integrity | All pass | [x] |

## Feature behavior (how the features work)

**F4 — Quality Audit.** Runs `audit_dataset()` (Phase 0 engine) on the dataset — and on its baseline when available. Returns per-metric before/after values + interpretation. The dashboard (Phase 4) renders this; **the numbers are the real computation, never faked** — this is the hero screenshot of the submission.

**F5 — Disclosure Receipt.** The receipt is generated from *actual run state*: which LLM mode ran (`real`/`mock`), which Adaption mode (`real`/`emulated`), what was generated vs. what the student supplied, oversight level (`prompt_guided` — the student prompted and reviewed; never `fully_autonomous` in our design), student contribution log, sources consulted (empty in mock — stated honestly), timestamp + SHA-256 integrity hash. The receipt adopts C2PA's vocabulary so it speaks the industry's language (docs/02). **The receipt is the differentiator** — it's what turns "AI helped" into "here is exactly how, and here is what is mine."

**F6 — Export.** Bundles the dataset (with provenance column), the receipt, and an auto-drafted methodology summary into downloadable files — the "research-ready package."

**F11 — Contribution Log.** The backend records every student action (edit plan, pick refinement, correct rows) in the session; the receipt summarizes them, making the student's ownership visible and auditable.

## Testing
- **Metrics correctness:** compute audit on a hand-checked sample; assert engine values match expectations.
- **Receipt:** field completeness against schema; hash verifies; mode flags correct for mock vs real; **negative test** — receipt in mock mode contains no sources.
- **Export:** download all files; CSV opens in pandas with provenance intact; methodology mentions the actual plan.

## Validation (DoD)
- [x] F4 returns real before/after metrics with interpretations for all 5+ metrics
- [x] F5 receipt contains every contract field; hash verifiable; mode accurately reported
- [x] No fabricated sources in any receipt (test-enforced)
- [x] F6 export works end-to-end (dataset + receipt + methodology)
- [x] F11 contribution log populated by real student actions

## Results

**Implementation summary:**
- **3.1–3.3** — `GET /api/datasets/{id}/audit` (`services.audit_dataset`): real engine metrics on the current dataset; pairs each metric with the stored baseline (`before`/`after`); when no baseline exists, `before` mirrors `after` with an explicit note; plain-language interpretation per metric + distribution sanity + overall verdict.
- **3.4** — `POST /api/receipts` + new `receipt.py` (`build_receipt`): every contract field populated from actual run state — `research_question` from session meta, `dataset_source`, mode-accurate `ai_tools_used` (`llm-mock` / `adaption-emulated`), `generated_vs_student` split, `human_oversight_level: prompt_guided` (never `fully_autonomous`), `student_contributions`, `sources_consulted`, `timestamp`, `integrity_hash`.
- **3.5** — SHA-256 over canonical JSON of the fields payload (hash excluded from its own input); `verify_integrity()` recomputes on reload; tamper test confirms detection.
- **3.6** — F11: session contribution log (`contributions.json`) records real student actions — auto-logged `question_submitted`, `refinement_picked`, `plan_submitted`, `dataset_uploaded` + student-submitted actions via `POST /api/sessions/{sid}/contributions` (`plan_edited`, `row_corrected`, …); receipt lists them.
- **3.7** — F8 variants: `standard`, `journal-style` (COPE/Nature-style sections), `teacher-check` (one-page) — `render_variant()` produces distinct layouts from one receipt.
- **3.8** — F9: `sources_consulted` is empty in every mode (the pipeline never consults external sources); **negative test enforces no fabricated sources**.
- **3.9** — `GET /api/exports/{session_id}` → bundle of `dataset.csv` (provenance column preserved), `receipt.json`, `methodology.md`, served via `/api/exports/{sid}/{filename}` download endpoints with a filename allowlist.
- **3.10** — methodology draft via `llm.draft_methodology` (real and mock paths); markdown includes dataset provenance counts + mode labels; never overclaims (mode and absence of sources stated).
- **3.11** — `tests/test_phase3.py`: 20 tests (metrics vs manual spot-check, before/after, interpretations, receipt completeness, hash verify + tamper, no-fabricated-sources, variants, F11 log, export integrity, error paths).

**Validation evidence:**
- `pytest tests/ -q` → **70 passed, 1 skipped** (skip = real-mode test, no `LLM_API_KEY`; **mock/emulated is the verified baseline**).
- Live runtime (uvicorn, zero API keys):
  - Audit (invented dataset): all 5 metrics + distribution sanity + 7 interpretation lines incl. verdict.
  - Audit (augmented dataset): real before/after — completeness **0.917 → 1.000** (baseline had a missing value).
  - Receipt: all contract fields; hash `sha256:…`; `sources_consulted: []`; oversight `prompt_guided`; 3 auto-logged student actions + 1 submitted action.
  - Export: 3 files served (dataset.csv 413 B, receipt.json 1839 B, methodology.md 818 B); CSV opens with `provenance` header.
  - Error paths: audit unknown → 404; export unknown session → 404; export filename guard → 400.

## Tracking notes
- **Honesty gate:** receipts must never claim real LLM/Adaption usage when running in mock/emulated mode. The `mode` field + UI label are the enforcement.
- **Stretch handling:** F8 (variants), F9 (source honesty), and F11 (contribution log) all fit and are done — no drop needed.
