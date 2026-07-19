"""Tests for accounts setup page skip/dismiss behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_accounts_setup_dismissed_unblocks_ready_event(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    data = project / "data"
    data.mkdir()
    (data / "web_config.json").write_text(
        json.dumps({"accounts_setup_dismissed": True}),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.config.accounts_loader import accounts_ready_event

    # Reset module event for test isolation
    import src.config.accounts_loader as mod

    mod._accounts_ready_event = None
    event = accounts_ready_event()
    assert event.is_set()


def test_needs_accounts_setup_respects_dismiss(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    data = project / "data"
    data.mkdir()
    (data / "web_config.json").write_text(
        json.dumps({"accounts_setup_dismissed": True}),
        encoding="utf-8",
    )
    monkeypatch.setenv("TDM_PORT", "8080")
    monkeypatch.setenv("TDM_DATA_DIR", str(data))
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.web import app as web_app

    web_app._DATA_DIR = data
    web_app._WEB_CONFIG_FILE = data / "web_config.json"
    assert web_app._needs_accounts_setup() is False


def test_needs_accounts_setup_without_accounts(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    data = project / "data"
    data.mkdir()
    (data / "web_config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("TDM_PORT", "8080")
    monkeypatch.setenv("TDM_DATA_DIR", str(data))
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.web import app as web_app

    web_app._DATA_DIR = data
    web_app._WEB_CONFIG_FILE = data / "web_config.json"
    assert web_app._needs_accounts_setup() is True
