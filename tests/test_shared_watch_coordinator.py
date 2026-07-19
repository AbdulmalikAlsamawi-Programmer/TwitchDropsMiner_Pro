"""Tests for multi-account shared watch coordination."""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock

import pytest

from src.services.shared_watch_coordinator import (
    SHARED_WATCH_MAX_AGE_SEC,
    SharedWatchCoordinator,
    SharedWatchState,
)


@pytest.fixture
def shared_watch_file(tmp_path, monkeypatch):
    path = tmp_path / "shared_watch.json"
    monkeypatch.setattr(
        "src.services.shared_watch_coordinator.SHARED_WATCH_PATH",
        path,
    )
    return path


def test_publish_and_read_primary(shared_watch_file, monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8080")
    channel = MagicMock()
    channel.name = "StreamerOne"
    channel.id = 12345
    channel.game.name = "2XKO"

    SharedWatchCoordinator.publish(channel)
    state = SharedWatchCoordinator.read()

    assert state is not None
    assert state.channel_login == "streamerone"
    assert state.channel_id == 12345
    assert state.game_name == "2XKO"


def test_publish_skipped_for_child(shared_watch_file, monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8082")
    channel = MagicMock()
    channel.name = "ChildPick"
    channel.id = 99
    channel.game.name = "Game"

    SharedWatchCoordinator.publish(channel)
    assert not shared_watch_file.exists()


def test_schedule_next_watch(shared_watch_file, monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8080")
    channel = MagicMock()
    channel.name = "SyncCh"
    channel.id = 42
    channel.game.name = "Game"

    SharedWatchCoordinator.publish(channel)
    before = time.time()
    SharedWatchCoordinator.schedule_next_watch(59.0)
    state = SharedWatchCoordinator.read()

    assert state is not None
    assert state.next_watch_at >= before + 58


def test_resolve_channel_by_id_or_login(shared_watch_file, monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8082")
    state = SharedWatchState(
        channel_login="target",
        channel_id=777,
        game_name="2XKO",
        published_at=time.time(),
        next_watch_at=0.0,
    )
    by_id = MagicMock()
    by_id.id = 777
    by_id.name = "Target"
    channels = {777: by_id}

    assert SharedWatchCoordinator.resolve_channel(channels, state) is by_id

    by_login = MagicMock()
    by_login.id = 888
    by_login.name = "Target"
    assert SharedWatchCoordinator.resolve_channel({888: by_login}, state) is by_login


def test_stale_shared_state_ignored(shared_watch_file):
    state = SharedWatchState(
        channel_login="old",
        channel_id=1,
        game_name="Game",
        published_at=time.time() - SHARED_WATCH_MAX_AGE_SEC - 10,
        next_watch_at=0.0,
    )
    channel = MagicMock()
    channel.id = 1
    assert SharedWatchCoordinator.resolve_channel({1: channel}, state) is None


def test_try_get_shared_channel_for_child(shared_watch_file, monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8090")
    payload = {
        "channel_login": "leader",
        "channel_id": 500,
        "game_name": "2XKO",
        "published_at": time.time(),
        "next_watch_at": time.time() + 30,
    }
    shared_watch_file.write_text(json.dumps(payload), encoding="utf-8")

    game = MagicMock()
    game.name = "2XKO"
    channel = MagicMock()
    channel.id = 500
    channel.name = "Leader"
    channel.online = True
    channel.drops_enabled = True
    channel.game = game

    twitch = MagicMock()
    twitch.settings.sync_watch_across_accounts = True
    twitch.wanted_games = [game]
    twitch.can_watch.return_value = True

    picked = SharedWatchCoordinator.try_get_shared_channel({500: channel}, twitch)
    assert picked is channel


def test_instance_watch_offset_scales_with_port(monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8080")
    assert SharedWatchCoordinator.instance_watch_offset_sec() == 0.0
    monkeypatch.setenv("TDM_PORT", "8082")
    assert SharedWatchCoordinator.instance_watch_offset_sec() == pytest.approx(0.15)
    monkeypatch.setenv("TDM_PORT", "8138")
    assert SharedWatchCoordinator.instance_watch_offset_sec() == pytest.approx(29 * 0.15)
