"""Tests for shared language persistence across multi-account instances."""

from __future__ import annotations

import json
from unittest.mock import patch

from src.i18n import _


def test_sync_language_from_shared_settings(tmp_path, monkeypatch):
    from src.web import app as web_app

    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps({"language": "العربية"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.SETTINGS_PATH", settings_file)

    _.set_language("English")
    web_app._sync_language_from_shared_settings()

    assert _.current_language == "العربية"


def test_sync_language_skips_when_already_current(tmp_path, monkeypatch):
    from src.web import app as web_app

    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps({"language": "English"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.SETTINGS_PATH", settings_file)

    _.set_language("English")
    with patch.object(_, "set_language") as mock_set:
        web_app._sync_language_from_shared_settings()
        mock_set.assert_not_called()
