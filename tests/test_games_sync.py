"""Games to watch are manual-only (no auto select-all from inventory)."""

from __future__ import annotations

import inspect

from src.core.client import Twitch


def test_client_does_not_auto_sync_games_to_watch():
    source = inspect.getsource(Twitch._run)
    assert "_sync_all_games_to_watch" not in source


def test_sync_all_games_to_watch_removed():
    assert not hasattr(Twitch, "_sync_all_games_to_watch")
