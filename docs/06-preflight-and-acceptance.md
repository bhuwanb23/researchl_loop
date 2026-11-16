# 06 — Pre-Flight Checklist & Acceptance Criteria

**Goal:** everything verified *before* writing app code. Items checked on 16 Nov 2026.

## A. Pre-flight checklist (status recorded 16 Nov 2026)

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Python 3.13 + pip available | ✅ | Python 3.13.18, pip 26.2.2 |
| 2 | Node 20 + npm available | ✅ | Node v20.20.2, npm 10.8.2 (for Next.js fallback decision) |
| 3 | Backend deps install cleanly | ✅ | fastapi/uvicorn/pandas/scikit-learn/python-multipart/openai/pytest in `backend/requirements.txt`; installed in venv |
| 4 | Quality engine smoke test passes | ✅ | `backend/tests/test_quality.py` — dedup/diversity/completeness/label-coverage on synthetic sample |
| 5 | LLM API access | ⏳ **user to confirm** | Needs `LLM_API_KEY` + `LLM_BASE_URL`. Until then, MockLLM fallback keeps the demo alive (labeled) |
| 6 | Adaption API access | ⏳ **user to confirm** | Needs `ADAPTION_API_KEY`. Until then, `ADAPTION_MODE=emulated` (documented in receipt + UI) |
| 7 | Demo dataset templates defined | ✅ | 3 templates in `data/templates/` (see README) |
| 8 | Devpost registration + credits claim | ⏳ **user action** | Register via challenge page; claim $1000 Adaption credits via referral link |
| 9 | Repo initialized (git) | ✅ | `git init` done; `.gitignore` excludes `.env` |

## B. Acceptance criteria (Definition of Done) — per feature

| Feature | Done when… |
|---|---|
| **F1 Scope** | A vague question returns a valid, editable plan (type, variables, row count, plan text); refinements offered for vague inputs; errors handled gracefully |
| **F2 Invent** | A plan produces a validated dataset (schema-correct, range-checked, ≥90% non-duplicate) with every row tagged `synthetic`; UI warns clearly |
| **F3 Augment** | A 10–200-row messy CSV uploads, parses, cleans, augments to target size; original rows preserved and tagged; malformed CSV gives a helpful error |
| **F4 Audit** | Real computed metrics before/after for all 5 metrics; dashboard renders them with one-line interpretations; numbers match a manual check on a sample |
| **F5 Receipt** | Receipt auto-generated per run with all required fields (C2PA-style oversight level, tools, contributions, hash); JSON export works; receipt accurately reflects what actually ran (mock vs real) |
| **F6 Export** | One-click download of dataset + receipt + methodology; files open correctly |
| **F7–F12** | Included only if core F1–F6 pass; templates ensure a guaranteed demo path |

## C. Demo acceptance (the 90–120s video)
1. Open app → pick template → see scoped plan (F1/F7).
2. Invent dataset → see preview (F2).
3. Run audit → **before/after chart** is the hero shot (F4).
4. Generate receipt → show fields (F5).
5. Download package (F6) → closing line.
**Must work offline via MockLLM** so the video never breaks.

## D. Honesty gates (non-negotiable)
- [ ] Every synthetic/augmented row carries provenance in data + UI.
- [ ] Receipt states whether LLM/Adaption ran in real or mock mode.
- [ ] No hardcoded quality metrics — all computed.
- [ ] No fabricated sources in receipts — only genuinely consulted URLs.
- [ ] Devpost description states exactly which sponsor features were genuinely used.
