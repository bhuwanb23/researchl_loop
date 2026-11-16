"""
schemas.py — Pydantic data contracts for ResearchLoop.

Mirrors the API/data contracts in docs/05-architecture-and-api.md exactly.
Every row carries a provenance tag (synthetic | original | augmented) — the
honesty rule: nothing downstream can render a dataset without provenance.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Provenance(str, Enum):
    """How a row was created. Enforced on every dataset row."""

    SYNTHETIC = "synthetic"
    ORIGINAL = "original"
    AUGMENTED = "augmented"


class HumanOversight(str, Enum):
    """C2PA-style oversight vocabulary (see docs/02 literature review)."""

    FULLY_AUTONOMOUS = "fully_autonomous"
    PROMPT_GUIDED = "prompt_guided"
    HUMAN_VALIDATED = "human_validated"


class ResearchType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    DESCRIPTIVE = "descriptive"
    SURVEY = "survey"


class Variable(BaseModel):
    name: str
    type: Literal["numeric", "categorical", "text"]
    unit: str | None = None


class ScopeResult(BaseModel):
    """F1 — POST /api/scope response (docs/05)."""

    research_type: ResearchType
    variables: list[Variable]
    suggested_rows: int
    data_plan: str
    dataset_name: str
    refinements: list[str] = Field(default_factory=list)


class DatasetRow(BaseModel):
    values: dict[str, Any]
    provenance: Provenance


class Dataset(BaseModel):
    """F2/F3 — a stored dataset with provenance + mode flags."""

    model_config = ConfigDict(populate_by_name=True)

    dataset_id: str
    session_id: str
    name: str
    rows: list[DatasetRow]
    schema_: dict[str, Any] = Field(alias="schema")  # JSON key stays "schema" (docs/05)
    warning: str | None = None
    llm_mode: str
    adaption_mode: str


class AuditReport(BaseModel):
    """F4 — GET /api/datasets/{id}/audit response."""

    dataset_id: str
    metrics: dict[str, Any]
    interpretation: list[str] = Field(default_factory=list)


class ReceiptFields(BaseModel):
    """F5 — the disclosure receipt payload (C2PA/COPE-aligned)."""

    research_question: str
    dataset_source: Literal["invented", "uploaded", "augmented"]
    ai_tools_used: list[dict[str, str]]
    generated_vs_student: dict[str, str]
    human_oversight_level: HumanOversight = HumanOversight.PROMPT_GUIDED
    student_contributions: list[dict[str, Any]] = Field(default_factory=list)
    sources_consulted: list[str] = Field(default_factory=list)
    timestamp: str
    integrity_hash: str


class Receipt(BaseModel):
    receipt_id: str
    session_id: str
    dataset_id: str
    fields: ReceiptFields
    format: str = "json"
    variant: str = "standard"  # F8: standard | journal-style | teacher-check


class ReceiptRequest(BaseModel):
    """POST /api/receipts request (docs/05)."""

    session_id: str
    dataset_id: str
    source: Literal["invented", "uploaded", "augmented"]
    variant: str = "standard"


class ContributionRequest(BaseModel):
    """POST /api/sessions/{session_id}/contributions — F11 student action log."""

    action: str
    detail: str = ""


class HealthStatus(BaseModel):
    status: str
    llm_mode: str
    adaption_mode: str


# ---------------------------------------------------------------- request models (docs/05)

class ScopeRequest(BaseModel):
    """POST /api/scope request. `refinement` enables the F7 flow."""

    question: str
    session_id: str | None = None
    refinement: str | None = None


class InventRequest(BaseModel):
    """POST /api/datasets/invent request."""

    session_id: str
    plan: ScopeResult
    rows: int = 80


class AugmentRequest(BaseModel):
    """POST /api/datasets/augment request (CSV as base64)."""

    session_id: str
    csv: str
    target_rows: int = 100
    filename: str | None = None
