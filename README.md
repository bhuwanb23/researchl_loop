# ResearchLoop

**The first step between a research question and real, defensible student research.**

ResearchLoop is a data-first research starter for students: you drop in a rough research
question (or a small messy dataset), and it (1) **invents or augments a small dataset** with a
real before/after quality chart, and (2) gives you a **disclosure receipt** — exactly what the
AI did, what is yours, verifiable with one hash. No prior ML experience needed.

Built for the **ML Build Challenge 4.0** (ML Empowerment Foundation) with **Adaption Labs** and
**Rise Research**.

---

## 60-second demo

1. Open the app → pick the **"Study vs. scores"** template.
2. **Ask** — a scoped research plan appears (editable).
3. **Build** — a synthetic dataset is invented, all rows tagged `synthetic`.
4. **Audit** — real before/after quality metrics with plain-language interpretation.
5. **Receipt** — a disclosure receipt: tools used, your contributions, integrity hash.
6. **Export** — dataset + receipt + methodology, ready to hand in.

The whole flow runs **offline in mock mode** — no API keys required, and every receipt states
exactly which modes ran.

## Setup & run

Requires Python 3.11+ (developed on 3.13). No Node build step — the frontend is a static SPA.

```bash
# 1. Install backend dependencies
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Run (mock mode — zero configuration, the verified demo baseline)
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Open the app
#    http://localhost:8000
```

**Real LLM mode (optional):** create `.env` in the project root (see `backend/.env.example`):

```bash
LLM_BASE_URL=...      # OpenAI-compatible endpoint
LLM_API_KEY=...
LLM_MODEL=...
ADAPTION_API_BASE=... # Adaption API base (if credentials available)
ADAPTION_API_KEY=...
ADAPTION_MODE=real|emulated
```

Without keys, the app runs in **mock LLM + emulated Adaption** mode and says so everywhere
(top-bar badge, receipts, exports). It never pretends a real run happened.

## Architecture

```
Browser (static SPA, frontend/)
   │  fetch /api/* (docs/05 contract)
   ▼
FastAPI backend (backend/app/)
   ├── main.py         endpoints: scope, invent, augment, audit, receipts, exports
   ├── services.py     orchestration: validation, diversity retry, dedup, export
   ├── quality.py      real metrics: dedup, near-dup (TF-IDF), diversity, completeness…
   ├── receipt.py      F5 disclosure receipt + SHA-256 integrity hash + variants
   ├── llm.py          RealLLM (OpenAI-compatible) + labeled MockLLM fallback
   ├── adaption.py     Adaption Adaptive Data adapter (real HTTP | emulated)
   ├── schemas.py      Pydantic contracts (provenance mandatory on every row)
   ├── config.py       env loading + honest mode resolution
   └── storage.py      sessions, datasets, receipts, baseline audits, contributions
```

**Data honesty rules enforced in code:**
- every generated row is tagged `synthetic`; every augmented row `augmented`; originals preserved
- invalid rows are dropped, never silently "fixed"
- diversity is enforced by a real TF-IDF near-duplicate check (≤5%), with offset retries
- receipts report the actual modes that ran and never fabricate sources
- `human_oversight_level: prompt_guided` — never `fully_autonomous`

## API (v1, see docs/05 for full contract)

| Endpoint | Feature |
|---|---|
| `POST /api/scope` | F1 question → plan (+ F7 refinement) |
| `POST /api/datasets/invent` | F2 synthetic dataset generation |
| `POST /api/datasets/augment` | F3 clean + augment an uploaded CSV |
| `GET /api/datasets/{id}/audit` | F4 before/after quality metrics + interpretations |
| `POST /api/receipts` | F5 disclosure receipt (hash-verified) |
| `POST /api/sessions/{sid}/contributions` | F11 student action log |
| `GET /api/exports/{sid}` | F6 export bundle (CSV + receipt + methodology) |
| `GET /api/health` | live mode report |

## Testing

```bash
cd backend
.venv/bin/python -m pytest tests/ -q          # 73 tests (mock-mode baseline; 1 real-mode skip)

# scripted end-to-end + verification (server running on :8000)
python3 scripts/e2e_mock.py        # full flow, 3 templates
python3 scripts/e2e_augment.py     # messy CSV augment + before/after
python3 scripts/spotcheck_metrics.py  # hand-calculated metrics vs engine
python3 scripts/capture_demo.py     # records demo video + screenshots (Playwright)
```

## Project layout

```
researchloop/
├── backend/           FastAPI app + tests (Phases 1–3)
├── frontend/          static SPA: Ask → Build → Audit → Receipt → Export (Phase 4)
├── data/templates/    3 demo scenarios (F10)
├── data/samples/      messy demo CSVs for the augment path
├── scripts/           E2E, spot-check, demo capture, demo script
├── assets/            demo video, screenshots, receipt sample (submission assets)
└── docs/              research, literature, design docs + per-phase plans
```

## Status & honesty notes

- **Demo baseline:** mock LLM + emulated Adaption (verified end-to-end, zero API keys). Real
  LLM/Adaption integrations are implemented and unit-tested behind the same interface; they
  activate automatically when credentials are provided.
- **Metrics are real:** every audit number is computed (pandas/TF-IDF); a spot-check script
  proves three metrics against hand calculation.
- **No fabricated sources:** receipts list only sources genuinely consulted — none in this
  pipeline, stated honestly.
- Phase-by-phase evidence: `docs/plans/README.md` (master plan + dashboard) and `phase_0.md`…`phase_6.md`.
