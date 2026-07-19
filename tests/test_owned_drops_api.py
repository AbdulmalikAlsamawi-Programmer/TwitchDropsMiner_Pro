"""Tests for /api/owned-drops (per-account claimed drop history)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch


def _write_instances(project, instances):
    (project / "instances.json").write_text(json.dumps({"instances": instances}), encoding="utf-8")


def test_get_owned_drops_live_parallel(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "data").mkdir()
    (project / "data2").mkdir()

    _write_instances(
        project,
        [
            {"n": 1, "port": 8080, "data_dir": "data", "label": "acc1"},
            {"n": 2, "port": 8082, "data_dir": "data2", "label": "acc2"},
        ],
    )
    (project / "accounts.txt").write_text("acc1:pass:tok1:1\nacc2:pass:tok2:2\n", encoding="utf-8")

    monkeypatch.setattr("src.config.paths.PROJECT_ROOT", project)
    monkeypatch.setattr("src.web.app.PROJECT_ROOT", project)
    monkeypatch.setattr("src.web.app._INSTANCES_FILE", project / "instances.json")

    import src.web.app as web_app
    web_app._sibling_drops[1] = [{"reward": "Pack 1", "claimed": True, "status": "claimed"}]
    web_app._sibling_drops[2] = []

    from src.web.app import get_owned_drops

    result = asyncio.run(get_owned_drops(live=True))

    assert len(result["accounts"]) == 2
    assert result["live"] is True
    assert result["accounts"][0]["claimed_count"] == 1


def test_get_owned_drops_empty_registry(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    _write_instances(project, [])

    monkeypatch.setattr("src.config.paths.PROJECT_ROOT", project)
    monkeypatch.setattr("src.web.app.PROJECT_ROOT", project)
    monkeypatch.setattr("src.web.app._INSTANCES_FILE", project / "instances.json")

    from src.web.app import get_owned_drops

    result = asyncio.run(get_owned_drops(live=True))
    assert result == {"accounts": [], "live": True}


def test_drop_is_completed_and_export_lines(tmp_path):
    from src.services.owned_drops_service import (
        drop_is_completed,
        export_account_lines,
        instance_ns_with_completed_for_games,
    )

    assert drop_is_completed({"status": "ready", "claimed": False}) is True
    assert drop_is_completed({"status": "claimed", "claimed": True}) is True
    assert drop_is_completed({
        "progress_required": 60,
        "progress_current": 60,
        "claimed": False,
    }) is True
    assert drop_is_completed({
        "progress_required": 60,
        "progress_current": 30,
        "claimed": False,
    }) is False

    accounts = [
        {
            "n": 1,
            "drops": [{"game": "Overwatch", "status": "ready", "claimed": False}],
        },
        {
            "n": 2,
            "drops": [{"game": "Overwatch", "progress_required": 60, "progress_current": 10}],
        },
        {
            "n": 3,
            "drops": [{"game": "League of Legends", "status": "ready", "claimed": False}],
        },
    ]
    assert instance_ns_with_completed_for_games(accounts, {"Overwatch"}) == [1]
    assert instance_ns_with_completed_for_games(accounts, {"Overwatch", "League of Legends"}) == [1, 3]

    project = tmp_path / "proj"
    project.mkdir()
    (project / "accounts.txt").write_text(
        "alice:p:t1:1\n\n# skipped\nbob:p:t2:2\n",
        encoding="utf-8",
    )
    assert export_account_lines(project, [1, 2]) == [
        "alice:p:t1:1",
        "bob:p:t2:2",
    ]
    assert export_account_lines(project, [2]) == ["bob:p:t2:2"]


def test_export_owned_accounts_endpoint(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "accounts.txt").write_text("alice:p:t1:1\nbob:p:t2:2\n", encoding="utf-8")

    monkeypatch.setattr("src.web.app.PROJECT_ROOT", project)
    monkeypatch.setenv("TDM_PORT", "8080")

    from src.web.app import ExportOwnedAccountsRequest, export_owned_account_lines, export_owned_accounts

    resp = asyncio.run(
        export_owned_accounts(ExportOwnedAccountsRequest(instance_ns=[1, 2]))
    )
    assert resp.body.decode("utf-8") == "alice:p:t1:1\nbob:p:t2:2\n"

    json_resp = asyncio.run(
        export_owned_account_lines(ExportOwnedAccountsRequest(instance_ns=[1, 2]))
    )
    assert json_resp == {"lines": ["alice:p:t1:1", "bob:p:t2:2"], "count": 2}
