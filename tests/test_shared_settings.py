"""Tests for shared settings path and auto-select-all games sync."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config import paths


def test_settings_path_uses_primary_data_folder():
    assert paths.SETTINGS_PATH == paths.PROJECT_ROOT / "data" / "settings.json"
    assert paths.SETTINGS_PATH.name == "settings.json"


def test_save_keys_merges_without_clobbering_language(tmp_path: Path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps({"language": "العربية", "dark_mode": False, "connection_quality": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.settings.SETTINGS_PATH", settings_file)

    from src.config.settings import Settings

    s = Settings()
    s.dark_mode = True
    s.save_keys(frozenset({"dark_mode"}))

    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert data["language"] == "العربية"
    assert data["dark_mode"] is True


def test_sync_games_to_watch_updates_and_broadcasts(monkeypatch):
    from src.web.managers.settings import SettingsManager

    monkeypatch.setattr("src.web.managers.settings.asyncio.create_task", lambda coro: coro)

    settings = MagicMock()
    settings.games_to_watch = ["Old Game"]
    settings.language = "English"
    settings.reload_from_disk = MagicMock()
    broadcaster = MagicMock()
    manager = SettingsManager(broadcaster, settings, MagicMock())

    changed = manager.sync_games_to_watch(["Game A", "Game B"])

    assert changed is True
    assert settings.games_to_watch == ["Game A", "Game B"]
    settings.save_keys.assert_called_once()
    broadcaster.emit.assert_called_once()


def test_sync_games_to_watch_noop_when_unchanged():
    from src.web.managers.settings import SettingsManager

    settings = MagicMock()
    settings.games_to_watch = ["Game A"]
    broadcaster = MagicMock()
    manager = SettingsManager(broadcaster, settings, MagicMock())

    assert manager.sync_games_to_watch(["Game A"]) is False
    settings.save_keys.assert_not_called()
