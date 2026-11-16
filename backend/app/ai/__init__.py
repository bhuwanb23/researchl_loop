"""ai — LLM layer (real + mock), Adaption adapter, and the disclosure receipt builder."""

from . import adaption, llm, receipt
from .adaption import AdaptionClient, AdaptionError
from .llm import LLMError, MockLLM, RealLLM, get_llm
from .receipt import (
    VALID_VARIANTS,
    build_receipt,
    compute_integrity_hash,
    render_variant,
    verify_integrity,
)

__all__ = [
    "adaption", "llm", "receipt",
    "AdaptionClient", "AdaptionError",
    "LLMError", "MockLLM", "RealLLM", "get_llm",
    "VALID_VARIANTS", "build_receipt", "compute_integrity_hash",
    "render_variant", "verify_integrity",
]
