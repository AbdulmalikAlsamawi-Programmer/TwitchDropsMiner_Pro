"""Tests for drop progress cache floor on websocket updates."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.services import drop_minutes_cache


def test_update_minutes_does_not_regress_below_cache(monkeypatch):
    from src.models.drop import TimedDrop

    drop_minutes_cache._cache.clear()
    drop_minutes_cache.update("drop-1", 30)

    campaign = MagicMock()
    campaign._update_real_minutes = MagicMock()

    drop = TimedDrop.__new__(TimedDrop)
    drop.id = "drop-1"
    drop.name = "Ticket Reception"
    drop.required_minutes = 45
    drop.real_current_minutes = 30
    drop.extra_current_minutes = 0
    drop.campaign = campaign
    drop.is_claimed = False

    drop.update_minutes(3)

    assert drop.real_current_minutes == 30
    campaign._update_real_minutes.assert_not_called()


def test_get_cached_returns_stored_minutes():
    drop_minutes_cache._cache.clear()
    drop_minutes_cache.update("drop-x", 66)
    assert drop_minutes_cache.get_cached("drop-x") == 66
    assert drop_minutes_cache.get_cached("missing") == 0
