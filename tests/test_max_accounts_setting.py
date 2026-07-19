"""Tests for max_accounts setting in settings manager."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.config.settings import Settings
from src.web.managers.settings import SettingsManager


def test_max_accounts_update_resyncs_instances(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("src.web.managers.settings.asyncio.create_task", lambda coro: coro)
    project = tmp_path / "proj"
    project.mkdir()
    data_dir = project / "data"
    data_dir.mkdir()
    (project / "accounts.txt").write_text("a1:p:t1:1\na2:p:t2:2\na3:p:t3:3\n", encoding="utf-8")
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    mock_settings = MagicMock(spec=Settings)
    mock_settings.max_accounts = 100
    for attr in (
        "inventory_filters",
        "mining_benefits",
        "games_to_watch",
        "make_predictions",
    ):
        setattr(mock_settings, attr, {} if "filters" in attr or "benefits" in attr else [] if "games" in attr else False)

    manager = SettingsManager(AsyncMock(), mock_settings, MagicMock())
    manager.update_settings({"max_accounts": 2})

    assert mock_settings.max_accounts == 2
    instances = json.loads((project / "instances.json").read_text(encoding="utf-8"))
    assert len(instances["instances"]) == 2
