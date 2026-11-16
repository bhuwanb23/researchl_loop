"""
main.py — ResearchLoop FastAPI composition root.

Wires the HTTP layer (app.api.routes) into the FastAPI app and mounts the
static frontend. The app entry point stays `app.main:app`.

Endpoints (docs/05 contract):
    GET  /api/health                     → live mode report
    POST /api/scope                      → F1 (+F7)
    POST /api/datasets/invent           → F2
    POST /api/datasets/augment          → F3
    GET  /api/datasets/{id}/audit       → F4
    POST /api/receipts                   → F5
    POST /api/sessions/{sid}/contributions → F11
    GET  /api/exports/{sid}[/{file}]    → F6
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .core import config
from .api.routes import router

app = FastAPI(title="ResearchLoop", version="0.3.0", description="Data-first research starter for students")
app.include_router(router)


# Static serving hook — the frontend is a static SPA (no build step);
# FastAPI serves frontend/ directly, including index.html at "/".
_FRONTEND_DIR = config.PROJECT_ROOT / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
