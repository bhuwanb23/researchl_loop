# Phase 4 — Frontend (5 Screens)

**Status:** ✅ **Complete** · **Days:** 8–11 · **Features delivered:** all UI for F1–F6, F10, F12 (+ F8/F11 display) · **Stack locked:** static SPA (vanilla HTML/CSS/JS, no build step) served by FastAPI · **Blocks:** Phase 5

---

## Goals
- Implement the 5-screen flow that *is* the demo: Ask → Build → Audit → Receipt → Export
- Beginner-friendly, polished UI (15% UX weight); charts for the before/after dashboard
- Works fully offline in mock mode so the demo never breaks

## Requirements / prerequisites
- Phase 1–3 backend complete (API contract stable from `docs/05`)
- **Day-1 decision:** Next.js (better polish) vs static SPA served by FastAPI (zero build). Both consume the same API.

## Sub-phases & tasks

| ID | Task | Description | Acceptance | Status |
|---|---|---|---|---|
| 4.1 | App shell & routing | App skeleton; 5 screens wired; session_id maintained across screens | Flow navigates Ask → Build → Audit → Receipt → Export | [x] |
| 4.2 | **Screen 1 — Ask** | Question input + template picker (F10); render scoped plan card (F1); show refinement options (F7) | Plan card editable; refinements selectable and re-scope | [x] |
| 4.3 | **Screen 2 — Build** | Two paths: Invent (F2) with rows control + preview; Augment (F3) with CSV upload + preview | Both paths produce preview tables; synthetic/augmented warnings shown | [x] |
| 4.4 | **Screen 3 — Audit** | Before/after dashboard (F4): bar chart per metric + interpretations (F12 tooltips) | Charts render real API numbers; before/after visible | [x] |
| 4.5 | **Screen 4 — Receipt** | Receipt render (F5): fields, contribution log (F11), mode badge (real/mock), integrity hash; variant selector (F8) | Receipt matches API; mode badge visible; download receipt | [x] |
| 4.6 | **Screen 5 — Export** | Research-ready package (F6): dataset + receipt + methodology; one-click download; closing summary | Downloads all 3 files; summary screen matches the demo script | [x] |
| 4.7 | Styling & UX polish | Consistent design system; plain-language copy; loading/error states; responsive | No raw JSON visible; errors are human-readable | [x] |
| 4.8 | F12 — explainers | Tooltips on each metric and receipt field ("why this matters") | Present on all metrics/fields | [x] |
| 4.9 | Mock-mode demo script | Walk the full flow using templates only, no keys, and capture it as the demo video (or as the script for recording) | Full flow completes offline | [x] |

## Feature behavior (how the UI works)
- **Session:** a `session_id` is created on first visit; every screen's API call carries it, so datasets, audits, receipts, and exports link together.
- **Ask → Build:** the plan from Screen 1 is the input to Screen 2's invent path; choosing a template pre-fills the plan.
- **Build → Audit:** the created dataset is audited automatically; the before/after appears on Screen 3 (for augment, "before" = the uploaded original).
- **Audit → Receipt:** the receipt is generated from the actual run state and shown with the mode badge — the UI *never* hides whether the run was real or mock.
- **Receipt → Export:** the final screen is the payoff — a downloadable package and a one-line closing summary.

## Testing
- **Manual flow:** full 5-screen walkthrough on each of the 3 templates (mock mode).
- **Contract check:** every screen renders the exact API response (no invented UI data).
- **Offline test:** run with no `.env` — everything works.
- **Responsive:** check at 1280px and mobile width (if time).

## Validation (DoD)
- [x] All 5 screens functional, offline (mock mode)
- [x] Charts render real before/after metrics
- [x] Receipt displays mode badge + all fields; download works
- [x] Export downloads all 3 files
- [x] No raw JSON dumps in UI; error states are human-readable
- [x] Demo walkthrough (template flow) completes without errors

## Results

**Day-1 stack decision:** **static SPA** (vanilla HTML/CSS/JS, no build step) served by the existing FastAPI static mount. Rationale: zero build/deploy risk, zero CDN dependencies (works in offline preview), identical API contract — polish was achieved with a small, consistent design system instead of framework overhead.

**Implementation summary:**
- **4.1** — `frontend/index.html` + hash routing (`#ask`…`#export`); `session_id` created on first visit (crypto.randomUUID, persisted in localStorage), carried on every API call; top-bar mode badge from `/api/health`.
- **4.2** — Ask: 3 template chips (F10) pre-fill question + scope immediately; scoped plan card (research type, rows, dataset name, data plan — all editable, edits logged as `plan_edited` F11 actions); refinement chips re-scope (F7).
- **4.3** — Build: tabs for **Invent** (rows slider 10–200, warning banner + preview table) and **Augment** (CSV file picker → base64 → target rows, original/augmented tags in preview).
- **4.4** — Audit: metric cards with inline-SVG before/after bar charts (real API numbers), improved/held/worsened badges, distribution-sanity card, interpretation list.
- **4.5** — Receipt: auto-built on entry; renders all fields, mode badge (LLM/Adaption), contribution log, integrity hash, sources-honesty note; **variant selector** (standard / journal-style / teacher-check) re-renders layout; download button.
- **4.6** — Export: 3 file cards with per-file + "download all three" buttons (blob downloads from `/api/exports/...`), closing summary card with modes.
- **4.7** — `frontend/styles.css` design system (tokens, cards, badges, banners, toasts, loading/error states); responsive at mobile width.
- **4.8** — F12: CSS tooltips (`ⓘ`) on every metric and receipt field with "why this matters" copy.
- **4.9** — `scripts/demo_script.md`: template-only, zero-key walkthrough with timing and capture notes (video capture is Phase 5's asset step).
- **Backend:** `main.py` static mount now serves `frontend/` directly (no build step).

**Validation evidence:**
- `node --check frontend/app.js` → syntax OK.
- `pytest tests/ -q` → **73 passed, 1 skipped** (skip = real-mode test; mock is the verified baseline).
- `tests/test_frontend.py`: `/` serves the SPA (all 5 screens present), `styles.css`/`app.js` served with correct content types, `/api/*` routes unaffected by the `/` static mount.
- Live runtime (uvicorn, zero API keys): `GET /` 200 (5 screens), assets 200, then the exact SPA demo flow over HTTP — scope → invent (80 rows, all synthetic) → audit (6 metrics, 7 interpretations) → receipt (3 contributions, 0 sources, hash) → export (3 files 200). All green.

## Tracking notes
- **Decision locked at start:** static SPA chosen over Next.js — removes build/deploy risk entirely; the API contract is identical either way, and polish was delivered via the design system.
- **Demo-safety rule:** templates + mock mode make Screen 2 and Screen 3 deterministic — the recorded demo never relies on a free-text question.
