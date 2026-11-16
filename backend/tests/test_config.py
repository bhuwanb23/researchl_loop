"""1.1 — config: defaults load without .env; modes resolve honestly."""

import importlib
import os

import pytest

from app import config


def test_defaults_load_without_env(monkeypatch):
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "ADAPTION_API_BASE", "ADAPTION_API_KEY", "ADAPTION_MODE"):
        monkeypatch.delenv(key, raising=False)
    importlib.reload(config)
    assert config.llm_mode() == "mock"            # no key → mock
    assert config.adaption_mode() == "emulated"   # no creds → emulated
    assert config.SESSION_DIR.is_absolute()       # resolved against project root
    assert config.TEMPLATES_DIR.is_dir()


def test_mode_switching(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("ADAPTION_MODE", "real")
    monkeypatch.setenv("ADAPTION_API_BASE", "https://api.adaptionlabs.ai")
    monkeypatch.setenv("ADAPTION_API_KEY", "key-test")
    importlib.reload(config)
    assert config.llm_mode() == "real"
    assert config.adaption_mode() == "real"


def test_adaption_real_request_without_credentials_degrades_to_emulated(monkeypatch):
    """Asking for real mode without credentials must NOT pretend — it degrades."""
    monkeypatch.setenv("ADAPTION_MODE", "real")
    monkeypatch.delenv("ADAPTION_API_KEY", raising=False)
    monkeypatch.delenv("ADAPTION_API_BASE", raising=False)
    importlib.reload(config)
    assert config.adaption_mode() == "emulated"
