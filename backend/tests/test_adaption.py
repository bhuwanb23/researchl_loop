"""1.5 — Adaption adapter: mode switching, honest labels, real-mode error path."""

import importlib

import pandas as pd
import pytest

from app import config
from app.adaption import AdaptionClient, AdaptionError
from app.llm import MockLLM


def test_emulated_invent_delegates_and_labels():
    # Ensure emulated mode (no credentials in test env)
    importlib.reload(config)
    client = AdaptionClient()
    assert client.mode == "emulated"
    scope, _ = MockLLM().scope("Does study time affect exam scores?")
    rows, mode = client.invent(scope, 30)
    assert mode == "emulated"
    assert len(rows) == 30
    assert all(r.provenance == "synthetic" for r in rows)


def test_emulated_improve_cleans_and_augments():
    client = AdaptionClient()
    df = pd.DataFrame({
        "study_mode": ["group", "solo", "group"],
        "quiz_score": [60, None, 80],
    })
    out, mode = client.improve(df, 10)
    assert mode == "emulated"
    assert len(out) == 10
    assert "provenance" in out.columns
    assert out["quiz_score"].notna().all()  # cleaning filled the missing value


def test_real_mode_without_credentials_raises_honest_error():
    client = AdaptionClient()
    # Force the real path without credentials — must raise, not pretend
    client.mode = "real"
    client._base = ""
    client._key = ""
    scope, _ = MockLLM().scope("Does study time affect exam scores?")
    with pytest.raises(AdaptionError):
        client.invent(scope, 10)


def test_adaption_mode_config_respects_credentials():
    import os

    os.environ.pop("ADAPTION_API_KEY", None)
    os.environ["ADAPTION_MODE"] = "real"
    importlib.reload(config)
    assert config.adaption_mode() == "emulated"  # asked for real, no key → emulated
