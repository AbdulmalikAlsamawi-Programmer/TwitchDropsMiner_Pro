"""Tests for choosing the correct active campaign when multiple exist for one game."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, PropertyMock

from src.services.inventory_service import InventoryService


def _campaign(
    name: str,
    first_remaining: int | None,
    *,
    cid: str = "",
    ends_in_days: float = 7.0,
):
    campaign = MagicMock()
    campaign.name = name
    campaign.id = cid or name
    campaign.can_earn.return_value = True
    campaign.ends_at = datetime.now(timezone.utc) + timedelta(days=ends_in_days)
    if first_remaining is None:
        campaign.first_drop = None
        campaign.progress_drop = None
    else:
        drop = MagicMock()
        drop.required_minutes = 200
        drop.effective_watched_minutes = MagicMock(
            return_value=max(0, 200 - first_remaining)
        )
        type(drop).remaining_minutes = PropertyMock(return_value=first_remaining)
        campaign.first_drop = drop
        campaign.progress_drop = drop
    type(campaign).remaining_minutes = PropertyMock(return_value=first_remaining or 999999)
    return campaign


def test_get_active_campaign_uses_first_drop_remaining_not_campaign_max():
    twitch = MagicMock()
    twitch.wanted_games = True
    channel = MagicMock()
    twitch.watching_channel.get_with_default.return_value = channel

    reign = _campaign("Reign of Talon: S3 Launch", 9, cid="aaa-reign")
    owcs = _campaign("OWCS S2 Campaign 3", 24, cid="bbb-owcs")
    type(reign).remaining_minutes = PropertyMock(return_value=900)
    type(owcs).remaining_minutes = PropertyMock(return_value=60)

    twitch.inventory = [owcs, reign]

    service = InventoryService(twitch)
    result = service.get_active_campaign(channel)

    assert result is reign


def test_get_active_campaign_prefers_ending_soonest_when_remaining_tied():
    twitch = MagicMock()
    twitch.wanted_games = True
    channel = MagicMock()
    twitch.watching_channel.get_with_default.return_value = channel

    reign = _campaign(
        "Reign of Talon: S3 Launch",
        4,
        cid="aaa-reign",
        ends_in_days=3.0,
    )
    owcs = _campaign(
        "OWCS S2 Campaign 3",
        4,
        cid="bbb-owcs",
        ends_in_days=10.0,
    )
    reign.first_drop.name = "Blooming Spring"
    owcs.first_drop.name = "Time for Waffles Icon"
    twitch.inventory = [owcs, reign]

    service = InventoryService(twitch)
    result = service.get_active_campaign(channel)

    assert result is reign


def test_get_active_campaign_uses_inventory_order_when_fully_tied():
    twitch = MagicMock()
    twitch.wanted_games = True
    channel = MagicMock()
    twitch.watching_channel.get_with_default.return_value = channel

    ends = datetime.now(timezone.utc) + timedelta(days=5)
    reign = _campaign("Reign of Talon: S3 Launch", 4, cid="aaa-reign", ends_in_days=5.0)
    owcs = _campaign("OWCS S2 Campaign 3", 4, cid="bbb-owcs", ends_in_days=5.0)
    reign.ends_at = ends
    owcs.ends_at = ends
    reign.first_drop.name = "Blooming Spring"
    owcs.first_drop.name = "Time for Waffles Icon"
    twitch.inventory = [owcs, reign]

    service = InventoryService(twitch)
    result = service.get_active_campaign(channel)

    assert result is owcs


def test_is_active_campaign_matches_computed_winner():
    twitch = MagicMock()
    twitch.wanted_games = True
    channel = MagicMock()
    twitch.watching_channel.get_with_default.return_value = channel

    reign = _campaign(
        "Reign of Talon: S3 Launch",
        4,
        cid="aaa-reign",
        ends_in_days=2.0,
    )
    owcs = _campaign(
        "OWCS S2 Campaign 3",
        4,
        cid="bbb-owcs",
        ends_in_days=9.0,
    )
    reign.first_drop.name = "Blooming Spring"
    owcs.first_drop.name = "Time for Waffles Icon"
    twitch.inventory = [owcs, reign]

    service = InventoryService(twitch)
    assert service.is_active_campaign(reign, channel) is True
    assert service.is_active_campaign(owcs, channel) is False
