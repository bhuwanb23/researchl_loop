# 04 — Tech Stack Decision

**Project:** ResearchLoop · **Constraints:** 16-day build, small student team, beginner-friendly, no GPU, LLM-API based, must produce a live demo + repo for Devpost.

## Recommended stack (chosen)

| Layer | Choice | Why |
|---|---|---|
| **Backend** | **Python 3.13 + FastAPI + Uvicorn** | Fast to write, async-friendly, auto OpenAPI docs (helps the team), single language for data work |
| **Data processing** | **pandas + scikit-learn (TF-IDF)** | Real CSV parsing, cleaning, and *real* quality metrics (dedup, diversity, completeness) — no heavy models, CPU-only, installs in seconds |
| **LLM layer** | **OpenAI-compatible API client (env-configured)** | Works with any provider (OpenAI, Groq, OpenRouter, local, etc.) via `LLM_BASE_URL` + `LLM_API_KEY`. **MockLLM fallback** for offline demo/testing, clearly labeled |
| **Adaption integration** | **`adaption_client.py` adapter** | Calls Adaption's Adaptive Data workflow when credentials/config exist; falls back to a *documented local emulation* of the invent/improve flow. Honest labeling in the UI either way |
| **Frontend** | **Next.js 15 (React, app router)** — *if the team is comfortable with React*; otherwise **static HTML/JS single-page app served by FastAPI** | Next.js gives the cleanest 5-screen UX for the 15% UX score. The static fallback is zero-build and equally functional. **Decision at day 1: pick based on team's React experience — both backend contracts are identical** |
| **Charts** | **Recharts** (Next.js) or **Chart.js via CDN** (static) | Before/after bar charts for the quality dashboard |
| **Storage** | **In-memory per session + local filesystem** (SQLite optional) | Hackathon scope: datasets as CSV files under `data/`, no database server |
| **Testing** | **pytest** (backend) + manual flow scripts | Smoke tests for the quality engine (highest-risk logic) |

## Alternatives considered (and rejected)

| Alternative | Why rejected |
|---|---|
| Full Next.js + Python separately deployed (two services) | More deploy friction for a 16-day demo; prefer single backend serving/proxying |
| sentence-transformers / torch embeddings for diversity | Too heavy (torch install, RAM); TF-IDF cosine is a legitimate, real diversity/duplicate metric at this scale |
| LangChain/LangGraph | Overkill for 4 LLM steps; raw API client is simpler and more transparent |
| Running a fine-tuned model locally | Out of scope (see ideation exclusions); all generation via API + mock fallback |
| SQLite + ORM for sessions | Not needed at hackathon scale; files are simpler and more inspectable for judges |

## Environment & dependencies
- **Python 3.13** (verified in sandbox), **Node 20** (verified) — both present.
- `backend/requirements.txt`: fastapi, uvicorn, pandas, scikit-learn, python-multipart, openai (client), pytest, httpx.
- `.env.example` documents all config; **no secrets in the repo** (`.gitignore` covers `.env`).

## Non-negotiable stack rules
1. **Every LLM output is labeled** — synthetic/augmented tags live in the data itself (honesty rule from ideation).
2. **Metrics are real** — the audit engine computes actual numbers; no hardcoded scores.
3. **LLM/Adaption failures degrade gracefully** — mock fallbacks let the demo run offline; the receipt always reflects what actually ran.
