"""engine — the quality/audit metrics engine (real computations, no hardcoded numbers)."""

from . import quality
from .quality import (
    NEAR_DUPLICATE_THRESHOLD,
    audit_dataset,
    clean_dataset,
    completeness,
    diversity,
    duplicate_rate,
    label_coverage,
    near_duplicate_rate,
)

__all__ = [
    "quality", "NEAR_DUPLICATE_THRESHOLD", "audit_dataset", "clean_dataset",
    "completeness", "diversity", "duplicate_rate", "label_coverage",
    "near_duplicate_rate",
]
