"""
main.py — ResearchLoop FastAPI app.

- /api/health                    → live status + resolved modes (honesty report)
- POST /api/scope                → F1 (+F7 refinement)
- POST /api/datasets/invent      → F2
- POST /api/datasets/augment     → F3
- GET  /api/datasets/{id}/audit  → F4 (before/after metrics + interpretation)
- POST /api/receipts             → F5 (disclosure receipt)
- POST /api/sessions/{sid}/contributions → F11 (student action log)
- GET  /api/exports/{session_id} → F6 (export bundle)
- GET  /api/exports/{session_id}/{filename} → F6 file download
- OpenAPI docs at /docs
- Static file serving hook: mounts frontend/dist if it exists (Phase 4)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config, services
from .storage import Storage
from .schemas import (
    AugmentRequest,
    ContributionRequest,
    HealthStatus,
    InventRequest,
    ReceiptRequest,
    ScopeRequest,
)

app = FastAPI(title="ResearchLoop", version="0.3.0", description="Data-first research starter for students")

_EXPORT_FILES = {"dataset.csv", "receipt.json", "methodology.md"}


@app.get("/api/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        llm_mode=config.llm_mode(),
        adaption_mode=config.adaption_mode(),
    )


# ---------------------------------------------------------------- F1 / F7

@app.post("/api/scope")
def api_scope(req: ScopeRequest):
    try:
        scope, mode = services.scope_question(req.question, req.refinement)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    # F11: record the student's action + session context for F5/F6
    session_id = req.session_id or "sess-adhoc"
    services._record_student_action(session_id, "question_submitted", req.question)
    if req.refinement:
        services._record_student_action(session_id, "refinement_picked", req.refinement)
    try:
        Storage().save_session_meta(session_id, {
            "question": (req.refinement or req.question).strip(),
            "plan": scope.model_dump(mode="json"),
            "mode": mode,
        })
    except Exception:
        pass  # session context is best-effort; never blocks the flow
    return {**scope.model_dump(mode="json"), "mode": mode}


# ---------------------------------------------------------------- F2

@app.post("/api/datasets/invent")
def api_invent(req: InventRequest):
    try:
        dataset = services.invent_dataset(req.session_id, req.plan, req.rows)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    services._record_student_action(req.session_id, "plan_submitted", req.plan.data_plan)
    return dataset.model_dump(mode="json", by_alias=True)


# ---------------------------------------------------------------- F3

@app.post("/api/datasets/augment")
def api_augment(req: AugmentRequest):
    try:
        dataset = services.augment_dataset(req.session_id, req.csv, req.target_rows, req.filename)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    services._record_student_action(req.session_id, "dataset_uploaded", req.filename or "upload.csv")
    return dataset.model_dump(mode="json", by_alias=True)


# ---------------------------------------------------------------- F4: audit

@app.get("/api/datasets/{dataset_id}/audit")
def api_audit(dataset_id: str):
    try:
        report = services.audit_dataset(dataset_id)
    except services.ServiceError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return report.model_dump(mode="json")


# ---------------------------------------------------------------- F5: receipt

@app.post("/api/receipts")
def api_receipt(req: ReceiptRequest):
    try:
        receipt = services.build_receipt_safe(req.session_id, req.dataset_id)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return receipt.model_dump(mode="json")


# ---------------------------------------------------------------- F11: contributions

@app.post("/api/sessions/{session_id}/contributions")
def api_contribution(session_id: str, req: ContributionRequest):
    try:
        services.log_contribution(session_id, req.action, req.detail)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"session_id": session_id, "action": req.action, "detail": req.detail, "logged": True}


# ---------------------------------------------------------------- F6: exports

@app.get("/api/exports/{session_id}")
def api_export(session_id: str):
    try:
        return services.build_export(session_id)
    except services.ServiceError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/api/exports/{session_id}/{filename}")
def api_export_file(session_id: str, filename: str):
    if filename not in _EXPORT_FILES:
        raise HTTPException(status_code=400, detail="Unknown export file.")
    path = Storage()._session_dir(session_id) / "exports" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file not found — build the export first.")
    media = {"dataset.csv": "text/csv", "receipt.json": "application/json", "methodology.md": "text/markdown"}
    return FileResponse(path, media_type=media[filename], filename=filename)


# Static serving hook — the frontend is a static SPA (no build step);
# FastAPI serves frontend/ directly, including index.html at "/".
_FRONTEND_DIR = config.PROJECT_ROOT / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
