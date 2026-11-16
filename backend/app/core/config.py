"""
config.py — environment loading and mode resolution for ResearchLoop.

Loads .env from the project root (if present) WITHOUT overriding variables
already set in the real environment. Mode resolution is the honesty
mechanism: `llm_mode()` and `adaption_mode()` report exactly what the app
will use, and nothing downstream ever assumes more than that.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # app/core/config.py → project root


def _load_env_file(path: Path) -> None:
    """Minimal .env parser: KEY=VALUE lines, comments (#), quotes stripped.

    Does NOT override variables already present in os.environ.
    """
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(PROJECT_ROOT / ".env")

# LLM layer (OpenAI-compatible)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Adaption integration
ADAPTION_API_BASE = os.getenv("ADAPTION_API_BASE", "")
ADAPTION_API_KEY = os.getenv("ADAPTION_API_KEY", "")
ADAPTION_MODE = os.getenv("ADAPTION_MODE", "emulated")

# Storage
SESSION_DIR = Path(os.getenv("SESSION_DIR", "data/sessions"))
if not SESSION_DIR.is_absolute():
    SESSION_DIR = PROJECT_ROOT / SESSION_DIR

TEMPLATES_DIR = PROJECT_ROOT / "data" / "templates"


def llm_mode() -> str:
    """'real' if a usable API key is configured, else 'mock'."""
    return "real" if LLM_API_KEY else "mock"


def adaption_mode() -> str:
    """'real' only if explicitly requested AND credentials are present;
    otherwise 'emulated' — honest degradation, never a pretend-real run."""
    if ADAPTION_MODE == "real" and ADAPTION_API_BASE and ADAPTION_API_KEY:
        return "real"
    return "emulated"
