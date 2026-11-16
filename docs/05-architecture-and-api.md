# 05 — Architecture, Repo Layout & API Contract

## Repo layout

```
researchloop/
├── README.md                     # project overview + setup + status
├── .gitignore
├── .env.example                  # all config keys (no secrets)
├── docs/                         # research + planning (01-06)
│   ├── 01-challenge-research.md
│   ├── 02-literature-review.md
│   ├── 03-ideation.md
│   ├── 04-tech-stack.md
│   ├── 05-architecture-and-api.md   ← this file
│   └── 06-preflight-and-acceptance.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               # FastAPI app, routes, static serving
│   │   ├── config.py             # env loading
│   │   ├── schemas.py            # Pydantic data contracts (matches §Data contracts)
│   │   ├── llm.py                # LLM client + MockLLM
│   │   ├── adaption.py           # Adaption adapter + emulation fallback
│   │   ├── quality.py            # audit engine (dedup, diversity, completeness…)
│   │   ├── receipt.py            # disclosure receipt builder
│   │   └── services.py           # orchestration: scope → invent → augment → audit → export
│   └── tests/
│       └── test_quality.py       # metrics smoke tests (run pre-build)
├── frontend/                     # Next.js app or static SPA (day-1 decision)
├── data/
│   ├── templates/                # F10 demo scenarios (JSON)
│   └── samples/                  # demo CSVs for augmentation path
├── scripts/                       # utility scripts (seed demo data, demo flow)
└── assets/                        # screenshots, demo video, receipt samples (submission assets)
```

## Runtime architecture

```
Browser (5 screens) ──► FastAPI (backend/app/main.py)
                           ├── /api/scope        ── llm.scope()
                           ├── /api/datasets/invent   ── llm.invent() + adaption.invent()
                           ├── /api/datasets/augment ── quality.clean() + llm.augment()
                           ├── /api/datasets/{id}/audit ── quality.audit()
                           ├── /api/receipts     ── receipt.build()
                           └── /api/exports      ── bundle download
                                │
                                ├── LLM layer (llm.py): real API or MockLLM (labeled)
                                ├── Adaption layer (adaption.py): real client or emulation (labeled)
                                └── Quality engine (quality.py): pandas + TF-IDF metrics
```

## API contract (v1)

All endpoints under `/api`, JSON in/out, session identified by `session_id` (UUID).

### 1. `POST /api/scope` — F1 Question → Scope
```json
// Request
{ "question": "Does study time affect exam scores?", "session_id": "uuid" }
// Response
{
  "research_type": "regression",          // classification | regression | descriptive | survey
  "variables": [{"name": "study_hours", "type": "numeric", "unit": "hours/week"}],
  "suggested_rows": 80,
  "data_plan": "Generate synthetic student records with study hours, prior GPA, sleep hours, and exam score; label score band as classification target.",
  "dataset_name": "study_vs_scores",
  "refinements": ["How does sleep mediate study time and scores?"]  // F7
}
```

### 2. `POST /api/datasets/invent` — F2
```json
// Request
{ "session_id": "uuid", "plan": {...scope response...}, "rows": 80 }
// Response
{ "dataset_id": "d_xxx", "rows": [...each row tagged "provenance": "synthetic"...],
  "schema": {...}, "warning": "All rows are synthetic and must be labeled as such in any use." }
```

### 3. `POST /api/datasets/augment` — F3
```json
// Request
{ "session_id": "uuid", "csv": "<base64 csv>", "target_rows": 100 }
// Response
{ "dataset_id": "d_xxx", "rows": [...provenance: "original" | "augmented"...],
  "baseline_stats": {...}, "notes": "Augmented rows are variations of original rows, tagged as such." }
```

### 4. `GET /api/datasets/{dataset_id}/audit` — F4
```json
{
  "dataset_id": "d_xxx",
  "metrics": {
    "duplicate_rate": {"before": 0.12, "after": 0.01},
    "near_duplicate_rate": {"before": 0.15, "after": 0.02},
    "diversity": {"before": 0.71, "after": 0.42, "note": "lower mean pairwise similarity = more diverse"},
    "completeness": {"before": 0.88, "after": 0.97},
    "label_coverage": {"before": 0.90, "after": 1.0},
    "distribution_sanity": {"passed": true, "issues": []}
  },
  "interpretation": ["Diversity improved: mean similarity 0.71 → 0.42"]
}
```

### 5. `POST /api/receipts` — F5
```json
// Request
{ "session_id": "uuid", "dataset_id": "d_xxx", "source": "invented|uploaded|augmented" }
// Response
{
  "receipt_id": "r_xxx",
  "fields": {
    "research_question": "...",
    "dataset_source": "invented",
    "ai_tools_used": [{"tool": "llm-gpt-compatible", "purpose": "dataset generation"}],
    "generated_vs_student": {"generated": "100% of rows (synthetic)", "student": "question + plan edits"},
    "human_oversight_level": "prompt_guided",   // C2PA vocabulary
    "student_contributions": [{"action": "edited_rows", "count": 12}],
    "sources_consulted": ["...urls, only if genuinely consulted"],
    "timestamp": "2026-11-17T09:00:00Z",
    "integrity_hash": "sha256:..."
  },
  "pdf_or_json": "json"   // v1: JSON; PDF if time
}
```

### 6. `GET /api/exports/{session_id}` — F6
```json
{ "files": {"dataset.csv": "url", "receipt.json": "url", "methodology.md": "url"} }
```

## Data contracts (schemas.py — Pydantic)
- `ScopeResult`, `DatasetRow` (`provenance: enum{synthetic, original, augmented}`), `Dataset`,
  `AuditReport`, `Receipt`, `ReceiptField` — mirror the JSON above exactly.
- **Provenance is mandatory** on every row — the UI refuses to render a dataset without it.

## Key config (`.env.example`)
```
LLM_BASE_URL=            # OpenAI-compatible endpoint
LLM_API_KEY=
LLM_MODEL=               # e.g. gpt-4o-mini
ADAPTION_API_BASE=       # Adaption API base (if credentials available)
ADAPTION_API_KEY=
ADAPTION_MODE=real|emulated
SESSION_DIR=data/sessions
```
