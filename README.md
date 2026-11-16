# ResearchLoop

**Data-first research starter for students** — a student enters a rough research question (or a small messy dataset), and ResearchLoop invents/augments a usable dataset for it, audits its quality (before/after), and attaches a disclosure receipt — exporting a research-ready package (dataset + receipt + methodology).

**Built for:** ML Empowerment Build Challenge 4.0 (deadline Dec 1, 2026, 9:00 PM PT)
**Sponsors:** Adaption Labs (Adaptive Data) · Rise Research (AI-disclosure ethos)
**Organizer:** ML Empowerment Foundation

## Why this project (one line)
No tool exists that combines student-scale dataset invention/augmentation + automatic quality auditing + a per-artifact disclosure receipt — the exact verification gap that recent literature shows causes majority of AI-generated research to contain unsupported claims.

## Documentation (docs/)
1. `01-challenge-research.md` — challenge facts, timeline, judging, sponsors
2. `02-literature-review.md` — primary + secondary sources, gap analysis, novelty statement
3. `03-ideation.md` — concept, feature taxonomy (core/important/leveraged/stretch/excluded), specs
4. `04-tech-stack.md` — chosen stack, alternatives, rules
5. `05-architecture-and-api.md` — repo layout, runtime architecture, API/data contracts
6. `06-preflight-and-acceptance.md` — pre-flight status, acceptance criteria, honesty gates

## Quick start

```bash
# Backend (Python 3.13)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Config (see .env.example; no secrets in repo)
cp ../.env.example ../.env   # then fill in LLM / Adaption keys

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (day-1 decision: Next.js or static SPA served by FastAPI)
```

Without `LLM_API_KEY` / Adaption credentials, the app runs in **labeled mock mode** (MockLLM + emulated Adaptive Data) so the demo never breaks.

## Demo templates (`data/templates/`)
1. **study_vs_scores** — "Does study time affect exam scores?" (regression + classification)
2. **plant_heat_tolerance** — "Which local plant species tolerates heat best?" (descriptive/ecology)
3. **group_study** — "Do students who study in groups score higher?" (survey-style)

## Status
- [x] Research, literature, ideation, stack, architecture, pre-flight
- [x] Quality engine smoke test (dedup/diversity/completeness/label-coverage)
- [ ] Backend implementation (F1–F6)
- [ ] Frontend implementation (5 screens)
- [ ] Demo video + screenshots (`assets/`)
- [ ] Devpost submission
