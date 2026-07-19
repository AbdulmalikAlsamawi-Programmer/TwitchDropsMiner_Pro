"""Tests for campaign progress manager complete-state payload."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

from src.web.managers.campaigns import CampaignProgressManager


def test_get_current_drop_uses_progress_drop_not_stale_completed():
    mgr = CampaignProgressManager(MagicMock())
    stale = MagicMock()
    stale.id = "waffles"
    stale.name = "Time for Waffles Icon"
    stale.required_minutes = 60
    type(stale).current_minutes = PropertyMock(return_value=60)
    type(stale).progress = PropertyMock(return_value=1.0)
    stale.is_claimed = False

    active = MagicMock()
    active.id = "bp-a"
    active.name = "BP Tier Skip S2.C3.A"
    active.required_minutes = 180
    type(active).current_minutes = PropertyMock(return_value=83)
    type(active).remaining_minutes = PropertyMock(return_value=97)
    type(active).progress = PropertyMock(return_value=83 / 180)
    active.is_claimed = False
    active.campaign.name = "OWCS S2 Campaign 3"
    active.campaign.id = "owcs"
    active.campaign.game.name = "Overwatch"

    stale.campaign = active.campaign
    stale.campaign.progress_drop = active

    mgr._current_drop = stale
    mgr._remaining_seconds = 0

    payload = mgr.get_current_drop()

    assert payload is not None
    assert payload["drop_name"] == "BP Tier Skip S2.C3.A"
    assert payload["watch_complete"] is False
    assert payload["current_minutes"] == 83


def test_drop_payload_marks_watch_complete():
    mgr = CampaignProgressManager(MagicMock())
    drop = MagicMock()
    drop.id = "drop-1"
    drop.name = "Pool Party Avatar Items"
    drop.campaign.name = "2XKO Evo 2026"
    drop.campaign.id = "camp-1"
    drop.campaign.game.name = "2XKO"
    drop.required_minutes = 30
    drop.is_claimed = False
    type(drop).current_minutes = PropertyMock(return_value=33)
    type(drop).progress = PropertyMock(return_value=1.0)

    payload = mgr._drop_payload(drop, remaining_seconds=-180)

    assert payload["watch_complete"] is True
    assert payload["current_minutes"] == 30
    assert payload["remaining_seconds"] == 0
