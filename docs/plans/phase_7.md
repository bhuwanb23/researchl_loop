# Phase 7 — UI Redesign (astryx-inspired) + File Organization

**Status:** ✅ **Complete** · **Trigger:** user's buildability + polish critique after Phase 6 · **Goal:** make the UI first and foremost beautiful, and organize all files into proper sub-folder hierarchies — frontend **and** backend
**Blocks:** nothing — polish pass on the completed Phase 1–6 system

---

## Goals

1. **Redesign the UI to be very beautiful, first priority.** Inspiration: Meta's open-source
   [astryx](https://github.com/meta/astryx) design system — refined neutral surfaces, precise
   typography, subtle elevation, blue accents, dark-mode polish — plus ResearchLoop's own
   **unique touches** that no other entry has.
2. **Proper file organization** — clear sub-files / sub-folders hierarchy, not one flat place,
   for **both frontend and backend**.
3. **Keep the working system intact**: F1–F6 features, mock-mode offline demo baseline, receipt
   honesty gates. UI must remain fully functional offline in mock mode.

## Unique ResearchLoop design touches (beyond the astryx base)

- **Pipeline arc stepper** — the five pipeline stages (Ask → Build → Audit → Receipt → Export)
  joined by segments; the active node pulses with the accent glow and completed segments light
  up the gradient. Clicking any step navigates there. This is the signature element.
- **Verified-document receipt panel** — the disclosure receipt renders as a perforated,
  sealed document (dashed separators, "✓ VERIFIED RECEIPT" seal, integrity hash bar),
  making the honesty gate feel like a real certificate rather than a JSON dump.
- **Before/after bar comparison** — every quality metric shows the messy baseline (muted gray
  with dashed edge) behind the delivered value (green gradient) in one row.
- **Mode chip (honesty gate)** — a persistent top-bar chip states mock vs live mode with a
  status dot; the receipt re-states the run mode. Never hidden.

## Design system (tokens.css)

- Dark neutral scale (`#0a0c10` → `#1e232d`), ambient radial mesh background
- Accent gradient: Meta blue `#2e6bff` → violet `#7b5cff`
- Subtle elevation (two-layer shadows), 12/18/24px radius scale, tabular-numeric metric values
- Restrained motion (120–320ms), responsive at 760px and 620px breakpoints
- Font stack: system sans + monospace for all numbers/hashes

## Sub-phases & tasks

| ID | Task | Description | Acceptance | Status |
|---|---|---|---|---|
| 7.1 | Backend reorganization | Split flat `backend/app/*.py` into `core/` (config, schemas, storage), `engine/` (quality), `ai/` (llm, adaption, receipt), `services/`, `api/` (routes) + package `__init__.py` re-exports; slim `main.py` becomes the composition root | All 74 tests pass; E2E scripts pass; import entry points preserved (`app.main:app`, `app.core/engine/ai/services`) | [x] |
| 7.2 | Frontend reorganization | Split flat `frontend/` into `css/` (tokens, base, components), `js/` (api, ui, stepper, main router), `js/views/` (one module per screen); delete old `app.js` + `styles.css` | New structure served correctly; all views render via the router | [x] |
| 7.3 | Design tokens & shell | `tokens.css` (astryx-inspired dark scale + accent gradient), `base.css` (topbar, pipeline arc, layout), `components.css` (cards, buttons, forms, badges, charts, table, receipt) | Tokens applied; no magic values in components | [x] |
| 7.4 | Screen redesigns | All 5 screens rebuilt on the new system: Ask (templates + refinement), Build (invent + augment with sample chips), Audit (before/after bars + reading + detail table), Receipt (verified-document panel + variant selector + action log), Export (file cards + download-all) | Full browser walkthrough passes; no console errors | [x] |
| 7.5 | API alignment | Frontend now matches the real response shapes: `InventRequest.rows` (separate from the scope object), `ReceiptRequest` source/variant, `AuditReport.metrics{before,after}`, export `files` map; added `GET /api/samples/{filename}` for one-click demo samples | All screens render real API data; sample route serves demo CSVs | [x] |
| 7.6 | Receipt endpoint F8 | `POST /api/receipts` now honors `variant` (standard/journal-style/teacher-check); source is derived server-side from row provenance (honesty) | Variant re-sign works; source never client-invented | [x] |
| 7.7 | Session consistency | Unified session id across all screens via `getSession()` (localStorage) so invent/augment/export/receipt share one session | Export finds the built dataset | [x] |
| 7.8 | Demo assets refresh | Re-captured demo video + 7 screenshots with `capture_demo.py` (updated for the new UI); `demo_timings.json` refreshed | Fresh assets committed; flow video ~18s | [x] |
| 7.9 | Docs sync | README project layout + design note; `docs/05` structure diagram + sample route; this plan | Docs match the repo | [x] |

## Validation (all run after the refactor)

- `pytest tests/ -q` → **74 passed, 1 skipped** (import entry points preserved)
- `scripts/e2e_mock.py` → **ALL 3 TEMPLATES PASS**
- `scripts/e2e_augment.py` → **ALL SAMPLES PASS**
- `scripts/spotcheck_metrics.py` → **ALL METRICS MATCH HAND CALCULATION**
- Playwright walkthrough (full 5-screen flow + augment sample) → all steps pass, **zero console errors**
- `scripts/capture_demo.py` → fresh `assets/demo_video.webm` + 7 screenshots

## Results

- Backend: `backend/app/{core,engine,ai,services,api}/` packages; `main.py` = 25-line composition root.
- Frontend: `frontend/{css/,js/,js/views/}` — tokenized design system + modular SPA.
- UI: astryx-inspired dark design system with the pipeline arc + verified-document receipt as
  unique signature touches. Fully functional offline in mock mode (honesty chip always visible).
- Assets refreshed: `assets/demo_video.webm` (3.1 MB), `assets/screenshots/01–07` (new UI).

## Tracking notes

- Two real defects surfaced and were fixed during the pass: a JS parse error (unescaped
  apostrophe in a placeholder) and an unbalanced call in the dataset preview builder — both
  caught by the browser walkthrough, reinforcing that the Playwright walkthrough is the real
  gate for frontend changes.
- The augment API expects **base64 CSV**; the new frontend encodes before sending (same as the
  Phase 4 frontend) — worth keeping in mind for any future augment-screen changes.
- Historical phase docs (0–6) are left as history; this phase is the polish + organization pass.
