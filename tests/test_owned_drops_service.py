"""Tests for owned drops collection and live inventory parsing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.owned_drops_service import (
    collect_owned_drops,
    enrich_entry_benefits,
    load_drops_history,
    merge_drops,
    parse_inventory_owned,
    sync_owned_drops_history,
)


def _mock_campaign(game: str, drop_name: str, reward: str, claimed: bool, benefit_id: str):
    benefit = MagicMock()
    benefit.id = benefit_id
    benefit.image_url = "https://example.com/img.jpg"
    benefit.name = reward

    drop = MagicMock()
    drop.is_claimed = claimed
    drop.name = drop_name
    drop.id = f"drop-{benefit_id}"
    drop.benefits = [benefit]
    drop.rewards_text.return_value = reward
    drop.required_minutes = 60
    drop.current_minutes = 60 if claimed else 10

    campaign = MagicMock()
    campaign.name = "Campaign"
    campaign.game.name = game
    campaign.drops = [drop]
    return campaign


def test_merge_drops_prefers_claimed():
    locked = {
        "game": "G",
        "drop": "D",
        "reward": "R",
        "claimed": False,
        "status": "in_progress",
        "timestamp": "2026-06-02T10:00:00+00:00",
    }
    claimed = {
        "game": "G",
        "drop": "D",
        "reward": "R",
        "claimed": True,
        "status": "claimed",
        "timestamp": "2026-06-01T10:00:00+00:00",
    }
    merged = merge_drops([locked], [claimed])
    assert len(merged) == 1
    assert merged[0]["claimed"] is True


def test_parse_inventory_owned_claimed_and_in_progress():
    inventory = {
        "gameEventDrops": [{"id": "b1", "lastAwardedAt": "2026-06-26T10:00:00Z"}],
        "dropCampaignsInProgress": [
            {
                "name": "Two Point Ten: Drops",
                "game": {"displayName": "Two Point Hospital"},
                "timeBasedDrops": [
                    {
                        "id": "d1",
                        "name": "Leaflet",
                        "requiredMinutesWatched": 120,
                        "self": {"isClaimed": True, "currentMinutesWatched": 120},
                        "benefitEdges": [
                            {
                                "benefit": {
                                    "id": "b1",
                                    "name": "Leaflet Info Stand",
                                    "imageAssetURL": "https://example.com/a.jpg",
                                }
                            }
                        ],
                    },
                    {
                        "id": "d2",
                        "name": "Milk",
                        "requiredMinutesWatched": 60,
                        "self": {"isClaimed": False, "currentMinutesWatched": 30},
                        "benefitEdges": [
                            {
                                "benefit": {
                                    "id": "b2",
                                    "name": "Milk Keg",
                                    "imageAssetURL": "https://example.com/b.jpg",
                                }
                            }
                        ],
                    },
                ],
            }
        ],
    }
    entries = parse_inventory_owned(inventory, {})
    by_reward = {e["reward"]: e for e in entries}
    assert by_reward["Leaflet Info Stand"]["claimed"] is True
    assert by_reward["Leaflet Info Stand"]["status"] == "claimed"
    assert by_reward["Milk Keg"]["status"] == "in_progress"
    assert by_reward["Milk Keg"]["progress_current"] == 30


def test_parse_inventory_owned_includes_multiple_benefits():
    inventory = {
        "gameEventDrops": [],
        "dropCampaignsInProgress": [
            {
                "name": "2XKO Evo 2026",
                "game": {"displayName": "2XKO"},
                "timeBasedDrops": [
                    {
                        "id": "pool-party",
                        "name": "Pool Party Avatar Items",
                        "requiredMinutesWatched": 30,
                        "self": {"isClaimed": False, "currentMinutesWatched": 30},
                        "benefitEdges": [
                            {
                                "benefit": {
                                    "id": "b1",
                                    "name": "Ahri's Lifeguard Visor",
                                    "imageAssetURL": "https://example.com/ahri.png",
                                }
                            },
                            {
                                "benefit": {
                                    "id": "b2",
                                    "name": "Darius's Life Vest",
                                    "imageAssetURL": "https://example.com/darius.png",
                                }
                            },
                            {
                                "benefit": {
                                    "id": "b3",
                                    "name": "Caitlyn's Sun Hat",
                                    "imageAssetURL": "https://example.com/caitlyn.png",
                                }
                            },
                        ],
                    }
                ],
            }
        ],
    }
    entries = parse_inventory_owned(inventory, {})
    assert len(entries) == 1
    entry = entries[0]
    assert entry["drop"] == "Pool Party Avatar Items"
    assert entry["status"] == "ready"
    assert len(entry["benefits"]) == 3
    assert entry["benefits"][0]["name"] == "Ahri's Lifeguard Visor"


def test_enrich_entry_benefits_from_cache():
    cache = {
        "b1": {
            "name": "Ahri's Lifeguard Visor",
            "image_url": "https://example.com/ahri.png",
            "game": "2XKO",
            "drop": "Pool Party Avatar Items",
        },
        "b2": {
            "name": "Darius's Life Vest",
            "image_url": "https://example.com/darius.png",
            "game": "2XKO",
            "drop": "Pool Party Avatar Items",
        },
    }
    entry = {
        "game": "2XKO",
        "drop": "Pool Party Avatar Items",
        "reward": "Ahri's Lifeguard Visor, Darius's Life Vest",
    }
    enriched = enrich_entry_benefits(entry, cache)
    assert len(enriched["benefits"]) == 2
    assert enriched["benefits"][1]["image_url"] == "https://example.com/darius.png"


def test_collect_owned_drops_from_claimed_campaigns(tmp_path):
    awarded = datetime(2026, 6, 26, 12, 0, tzinfo=timezone.utc)
    campaign = _mock_campaign("Two Point Hospital", "Week 1", "Leaflet Info Stand", True, "b1")
    claimed_benefits = {"b1": awarded}

    drops = collect_owned_drops(tmp_path, [campaign], claimed_benefits)
    assert len(drops) == 1
    assert drops[0]["reward"] == "Leaflet Info Stand"
    assert drops[0]["claimed"] is True


def test_load_drops_history_reads_account_subfolders(tmp_path):
    account_dir = tmp_path / "accounts" / "tunpx11"
    account_dir.mkdir(parents=True)
    entry = [{"timestamp": "2026-06-26T12:00:00+00:00", "game": "G", "drop": "D", "reward": "R", "claimed": True}]
    (account_dir / "drops_history.json").write_text(json.dumps(entry), encoding="utf-8")

    loaded = load_drops_history(tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["reward"] == "R"


def test_fetch_all_owned_drops_parallel(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "data").mkdir()
    (project / "data2").mkdir()
    instances = [
        {"n": 1, "port": 8080, "data_dir": "data", "label": "a1"},
        {"n": 2, "port": 8082, "data_dir": "data2", "label": "a2"},
    ]

    async def fake_fetch(data_dir, instance_n):
        return [
            {
                "game": "G",
                "drop": f"D{instance_n}",
                "reward": f"R{instance_n}",
                "claimed": True,
                "status": "claimed",
            }
        ]

    import asyncio

    monkeypatch.setattr("src.services.owned_drops_service.fetch_owned_drops_live", fake_fetch)
    from src.services.owned_drops_service import fetch_all_owned_drops

    result = asyncio.run(fetch_all_owned_drops(instances))
    assert len(result) == 2
    assert result[0]["claimed_count"] == 1
    assert result[1]["drops"][0]["reward"] == "R2"
