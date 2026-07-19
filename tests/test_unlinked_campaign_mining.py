"""Unlinked campaigns can be mined when selected in games_to_watch."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.models.campaign import DropsCampaign


def _campaign_data(*, linked: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    drop_start = start
    drop_end = end
    return {
        "id": "campaign-ow",
        "name": "OWCS Test",
        "game": {
            "id": "488552",
            "name": "Overwatch",
            "displayName": "Overwatch",
            "boxArtURL": "https://example.test/ow-{width}x{height}.jpg",
        },
        "self": {"isAccountConnected": linked},
        "accountLinkURL": "https://example.test/link",
        "startAt": start,
        "endAt": end,
        "status": "ACTIVE",
        "allow": {"channels": [], "isEnabled": True},
        "timeBasedDrops": [
            {
                "id": "drop-1",
                "name": "Drop 1",
                "startAt": drop_start,
                "endAt": drop_end,
                "benefitEdges": [
                    {
                        "benefit": {
                            "id": "b1",
                            "name": "Skin",
                            "distributionType": "DIRECT_ENTITLEMENT",
                            "imageAssetURL": "https://example.test/skin.png",
                        }
                    }
                ],
                "preconditionDrops": [],
                "requiredSubs": 0,
                "requiredMinutesWatched": 120,
                "self": {
                    "dropInstanceID": None,
                    "isClaimed": False,
                    "currentMinutesWatched": 0,
                },
            }
        ],
    }


def test_unlinked_campaign_is_eligible_and_can_earn_within():
    campaign = DropsCampaign(MagicMock(), _campaign_data(linked=False), {})
    next_hour = datetime.now(timezone.utc) + timedelta(hours=1)

    assert campaign.linked is False
    assert campaign.eligible is True
    assert campaign.can_earn_within(next_hour) is True
    assert campaign.has_wanted_unclaimed_benefits(
        {"DIRECT_ENTITLEMENT": True, "BADGE": True, "EMOTE": True, "UNKNOWN": True}
    )


def test_linked_status_preserved_for_ui():
    linked = DropsCampaign(MagicMock(), _campaign_data(linked=True), {})
    unlinked = DropsCampaign(MagicMock(), _campaign_data(linked=False), {})
    assert linked.linked is True
    assert unlinked.linked is False
