"""Tests for per-instance runtime status persistence."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from src.utils.instance_runtime import (
    load_runtime_watching,
    parse_is_watching,
    refresh_runtime_watching,
    save_runtime_status,
    set_active_drop,
)


def test_parse_is_watching_active_mining():
    assert parse_is_watching("Watching: shroud") is True
    assert parse_is_watching("🎯 Manual Mode: Watching shroud for 2XKO") is True
    assert parse_is_watching("shroud :يتم حالياَ مشاهدة") is True


def test_parse_is_watching_not_mining():
    assert parse_is_watching("Idle") is False
    assert parse_is_watching("💤 Idle watching: shroud") is False
    assert parse_is_watching("⏸ Mining paused") is False
    assert parse_is_watching(
        "All drops complete for configured games — stopping this account."
    ) is False
    assert parse_is_watching("No active campaigns to mine drops for. Waiting...") is False


def test_save_and_load_runtime_watching(tmp_path):
    save_runtime_status(tmp_path, "Watching: shroud")
    assert load_runtime_watching(tmp_path) is True

    save_runtime_status(tmp_path, "Idle")
    assert load_runtime_watching(tmp_path) is False


def test_refresh_runtime_watching_updates_timestamp(tmp_path):
    save_runtime_status(tmp_path, "Idle")
    first = json.loads((tmp_path / "runtime_status.json").read_text(encoding="utf-8"))
    refresh_runtime_watching(tmp_path, "Watching: shroud")
    second = json.loads((tmp_path / "runtime_status.json").read_text(encoding="utf-8"))
    assert second["watching"] is True
    assert second["updated_at"] != first["updated_at"]


def test_set_active_drop_persists_while_watching(tmp_path):
    save_runtime_status(tmp_path, "Watching: shroud")
    set_active_drop(
        tmp_path,
        {
            "drop_id": "drop-1",
            "drop_name": "Time for Waffles Icon",
            "game_name": "Overwatch",
            "campaign_name": "OWCS S2 Campaign 3",
        },
    )
    raw = json.loads((tmp_path / "runtime_status.json").read_text(encoding="utf-8"))
    assert raw["active_drop_id"] == "drop-1"
    assert raw["active_drop_name"] == "Time for Waffles Icon"
    assert raw["active_campaign"] == "OWCS S2 Campaign 3"
    assert raw["watching"] is True


def test_idle_status_clears_active_drop(tmp_path):
    set_active_drop(
        tmp_path,
        {"drop_id": "drop-1", "drop_name": "Ticket Reception", "game_name": "Two Point Museum"},
    )
    save_runtime_status(tmp_path, "Idle")
    raw = json.loads((tmp_path / "runtime_status.json").read_text(encoding="utf-8"))
    assert raw.get("active_drop_id") is None


def test_load_runtime_watching_stale_idle(tmp_path):
    path = tmp_path / "runtime_status.json"
    old = datetime.now(timezone.utc) - timedelta(seconds=300)
    path.write_text(
        json.dumps({"status": "Idle", "watching": False, "updated_at": old.isoformat()}),
        encoding="utf-8",
    )
    assert load_runtime_watching(tmp_path, max_age_sec=120.0) is False


def test_load_runtime_watching_old_status_still_watching(tmp_path):
    path = tmp_path / "runtime_status.json"
    old = datetime.now(timezone.utc) - timedelta(seconds=7200)
    path.write_text(
        json.dumps(
            {
                "status": "Watching: shroud",
                "watching": True,
                "updated_at": old.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    assert load_runtime_watching(tmp_path) is True
