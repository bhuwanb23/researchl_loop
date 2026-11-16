# Phase 1 — Backend Foundation

**Status:** 🔲 Not started · **Planned days:** 1–2 · **Features delivered:** none directly (enables F1–F6) · **Blocks:** Phase 2

---

## Goals
- Build the backend skeleton every feature plugs into: data contracts, config, LLM layer, Adaption adapter, dataset storage
- Make **mock mode** the default working state: the app must run end-to-end without any API keys
- Establish the session/dataset storage model so Phases 2–3 can read/write datasets

## Requirements / prerequisites
- Phase 0 complete (quality engine + contracts exist)
- `backend/requirements.txt` installed in venv (done)
- `.env.example` copied to `.env` (optional keys — mock mode works without)

## Sub-phases & tasks

| ID | Task | Description | Acceptance | Status |
|---|---|---|---|---|
| 1.1 | `config.py` | Env loading (`LLM_*`, `ADAPTION_*`, `SESSION_DIR`), defaults for mock mode | Loads without `.env`; `ADAPTION_MODE` switches cleanly | [x] |
| 1.2 | `schemas.py` | Pydantic models matching `docs/05` contracts: `ScopeResult`, `DatasetRow`, `Dataset`, `AuditReport`, `Receipt`, `ReceiptField` | Every contract type defined; provenance enum enforced | [x] |
| 1.3 | `llm.py` — LLM client | OpenAI-compatible client (`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`); `llm.scope()`, `llm.invent()`, `llm.augment()`, `llm.draft_methodology()` | Calls return structured data; errors handled; **never fabricates sources** | [x] |
| 1.4 | `llm.py` — MockLLM | Deterministic template-driven fallback for all 4 LLM methods; labeled `mode: "mock"` in output | Every method works offline with realistic output; mode flag present | [x] |
| 1.5 | `adaption.py` — Adaption adapter | Real client path (`ADAPTION_API_BASE`/`ADAPTION_API_KEY`) for Adaptive Data invent/improve; `ADAPTION_MODE=emulated` fallback that calls the LLM layer with the same workflow | Mode switch works; outputs labeled `real` or `emulated` | [x] |
| 1.6 | Storage layer | Session + dataset storage under `SESSION_DIR`: save/load CSV + metadata JSON per dataset_id; provenance preserved | Datasets persist across requests; rows keep provenance tags | [x] |
| 1.7 | `main.py` skeleton | FastAPI app; health endpoint; static file serving hook; OpenAPI at `/docs` | `uvicorn app.main:app` starts; `/api/health` returns OK | [x] |
| 1.8 | Unit tests — foundation | Tests for: schema validation, config defaults, MockLLM determinism, adapter mode switching, storage round-trip | All tests pass in mock mode | [x] |

## Feature behavior (how the foundation works)
- **LLM layer:** one interface, two implementations. `RealLLM` calls the configured OpenAI-compatible endpoint; `MockLLM` uses the template engine (driven by `data/templates/*.json` + rules). The app always asks `llm.get_mode()` and the receipt/UI record which ran. **This is the honesty mechanism** — nothing downstream ever assumes real generation happened.
- **Adaption layer:** `AdaptionClient.invent(plan)` / `.improve(df)` — in `real` mode it hits the Adaption API; in `emulated` mode it delegates to the LLM layer with the Adaption workflow semantics (generate-where-none-exists / clean-augment). The receipt records the mode.
- **Storage:** each dataset is a folder `data/sessions/{session_id}/{dataset_id}/` containing `rows.csv`, `metadata.json` (schema, provenance counts, mode flags). The receipt and export read from this.

## Testing
- Unit: schema validation rejects missing provenance; MockLLM is deterministic (same input → same output); adapter mode switch returns correct labels; storage round-trip preserves row tags.
- Integration (Phase 1 scope): `/api/health` responds; storage save→load returns identical CSV.

## Validation (DoD)
- [x] App boots with zero API keys (mock mode)
- [x] All schemas match `docs/05` contract exactly
- [x] MockLLM produces valid outputs for all 4 methods
- [x] Adaption adapter labels real vs emulated
- [x] Unit tests pass (32/32 total)

## Results

**Implemented (all files under `backend/app/`):**
- `config.py` — minimal `.env` parser (no new dependency), mode resolution: `llm_mode()` / `adaption_mode()`; honest degradation (real requested without creds → emulated)
- `schemas.py` — all contract models; `Provenance` enum enforced on every `DatasetRow`; `Dataset.schema` aliased to avoid pydantic shadowing (JSON key stays `"schema"`)
- `llm.py` — `RealLLM` (OpenAI-compatible, JSON mode, raises `LLMError` on failure — never silently degrades) + `MockLLM` (deterministic, template-driven, mode `"mock"`); `get_llm()` resolves per config
- `adaption.py` — `AdaptionClient` with `invent()` / `improve()`; real HTTP path via httpx (endpoint default documented as best-effort, to be confirmed against Adaption docs) + emulated delegation to the LLM layer; outputs labeled `real`/`emulated`
- `storage.py` — `Storage` with index-backed dataset/receipt save/load; provenance column persisted in `rows.csv`; metadata + provenance counts in `metadata.json`
- `main.py` — FastAPI app, `/api/health` (reports resolved modes), static-mount hook for `frontend/dist` (Phase 4)

**Templates extended:** `mock_ranges` / `mock_values` added to all 3 demo templates so MockLLM generates realistic, range-respecting data.

**Testing — 32/32 PASS (Phase 0: 6, Phase 1: 26):**
- config: defaults without `.env`, mode switching, honest degradation
- schemas: contract fields, provenance enum enforcement, receipt fields
- MockLLM: template matching (3/3), determinism, row counts, ranges respected, augment tagging, honest methodology
- adaption: emulated delegation + labels, real-mode error path, credential-aware config
- storage: round-trips preserve rows + provenance + metadata + receipts
- main: `/api/health` 200 + honest modes, `/docs` 200

**Runtime validation (zero API keys):**
- `uvicorn app.main:app` boots cleanly
- `GET /api/health` → `{"status":"ok","llm_mode":"mock","adaption_mode":"emulated"}`
- `GET /docs` → 200; OpenAPI JSON served
- Mock mode is the default working state — Phase 2 can build on it without any keys

## Tracking notes
- **RealLLM:** implemented and wired, but NOT exercised — no `LLM_API_KEY` in the environment. Real mode is opt-in via config; MockLLM remains the verified default. When a key is provided, re-run tests to confirm the real path (add to Phase 2's real-mode tests).
- **Adaption real path:** endpoint path is a best-effort default (`/api/v1/adaptive-data/{op}`) — must be confirmed against Adaption's API docs when credentials arrive. Emulated mode is verified and labeled.
- **Frontend direction (Next.js vs static SPA):** still open, affects Phase 4 only. Backend contract is identical either way.
- **Phase 1 verdict:** ✅ COMPLETE — all 8 tasks done, 32/32 tests, runtime validated in mock mode. Unblocks Phase 2.
