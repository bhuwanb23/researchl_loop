"""
routes.py — HTTP endpoint definitions (the /api contract, docs/05).

Endpoints:
    GET  /api/health                     → live mode report (honesty badge)
    POST /api/scope                      → F1 (+F7 refinement)
    POST /api/datasets/invent            → F2
    POST /api/datasets/augment           → F3
    GET  /api/datasets/{id}/audit        → F4
    POST /api/receipts                   → F5
    POST /api/sessions/{sid}/contributions → F11
    GET  /api/exports/{sid}              → F6
    GET  /api/exports/{sid}/{filename}   → F6 file download
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..core import config
from ..core.schemas import (
    AugmentRequest,
    ContributionRequest,
    HealthStatus,
    InventRequest,
    ReceiptRequest,
    ScopeRequest,
)
from ..core.storage import Storage
from ..services import services

router = APIRouter(prefix="/api")

_EXPORT_FILES = {"dataset.csv", "receipt.json", "methodology.md"}


# Demo sample CSVs (the augment flow needs a starting point; served read-only)
@router.get("/samples/{filename}", include_in_schema=False)
def sample_file(filename: str):
    if not filename.endswith(".csv") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Only .csv sample files are served.")
    path = config.PROJECT_ROOT / "data" / "samples" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sample not found.")
    return FileResponse(path, media_type="text/csv", filename=filename)


@router.get("/health")
def health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        llm_mode=config.llm_mode(),
        adaption_mode=config.adaption_mode(),
    )


# ---------------------------------------------------------------- F1 / F7

@router.post("/scope")
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

@router.post("/datasets/invent")
def api_invent(req: InventRequest):
    try:
        dataset = services.invent_dataset(req.session_id, req.plan, req.rows)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    services._record_student_action(req.session_id, "plan_submitted", req.plan.data_plan)
    return dataset.model_dump(mode="json", by_alias=True)


# ---------------------------------------------------------------- F3

@router.post("/datasets/augment")
def api_augment(req: AugmentRequest):
    try:
        dataset = services.augment_dataset(req.session_id, req.csv, req.target_rows, req.filename)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    services._record_student_action(req.session_id, "dataset_uploaded", req.filename or "upload.csv")
    return dataset.model_dump(mode="json", by_alias=True)


# ---------------------------------------------------------------- F4: audit

@router.get("/datasets/{dataset_id}/audit")
def api_audit(dataset_id: str):
    try:
        report = services.audit_dataset(dataset_id)
    except services.ServiceError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return report.model_dump(mode="json")


# ---------------------------------------------------------------- F5: receipt

@router.post("/receipts")
def api_receipt(req: ReceiptRequest):
    try:
        receipt = services.build_receipt_safe(req.session_id, req.dataset_id, variant=req.variant)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return receipt.model_dump(mode="json")


# ---------------------------------------------------------------- F11: contributions

@router.post("/sessions/{session_id}/contributions")
def api_contribution(session_id: str, req: ContributionRequest):
    try:
        services.log_contribution(session_id, req.action, req.detail)
    except services.ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"session_id": session_id, "action": req.action, "detail": req.detail, "logged": True}


# ---------------------------------------------------------------- F6: exports

@router.get("/exports/{session_id}")
def api_export(session_id: str):
    try:
        return services.build_export(session_id)
    except services.ServiceError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/exports/{session_id}/{filename}")
def api_export_file(session_id: str, filename: str):
    if filename not in _EXPORT_FILES:
        raise HTTPException(status_code=400, detail="Unknown export file.")
    path = Storage()._session_dir(session_id) / "exports" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file not found — build the export first.")
    media = {"dataset.csv": "text/csv", "receipt.json": "application/json", "methodology.md": "text/markdown"}
    return FileResponse(path, media_type=media[filename], filename=filename)
