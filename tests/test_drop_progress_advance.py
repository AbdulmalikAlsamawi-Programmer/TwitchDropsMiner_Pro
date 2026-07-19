"""Tests for drop progress bar advancing to the next drop in a chain."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, PropertyMock

import pytest

from src.models.campaign import DropsCampaign
from src.models.drop import TimedDrop


def _make_drop(
    *,
    drop_id: str,
    name: str,
    required: int,
    current: int,
    claimed: bool = False,
    preconditions: list[str] | None = None,
) -> MagicMock:
    drop = MagicMock(spec=TimedDrop)
    drop.id = drop_id
    drop.name = name
    drop.required_minutes = required
    drop.is_claimed = claimed
    drop.precondition_drops = preconditions or []
    drop.can_earn.return_value = not claimed and (
        not preconditions or all(False for _ in preconditions)
    )
    type(drop).remaining_minutes = PropertyMock(return_value=max(0, required - current))
    type(drop).current_minutes = PropertyMock(return_value=current)
    drop.effective_watched_minutes = MagicMock(return_value=current)
    drop._base_can_earn.return_value = not claimed
    return drop


def test_first_drop_prefers_in_progress_over_completed(monkeypatch):
    campaign = MagicMock(spec=DropsCampaign)
    done = _make_drop(drop_id="a", name="Drop A", required=30, current=30, claimed=False)
    done.can_earn.return_value = True
    next_drop = _make_drop(drop_id="b", name="Drop B", required=60, current=10, claimed=False)
    next_drop.can_earn.return_value = True
    campaign.drops = [done, next_drop]

    result = DropsCampaign.first_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is next_drop


def test_get_max_accounts_from_accounts_file(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "accounts.txt").write_text(
        "\n".join(f"user{i}:p:t{i}:{1000 + i}" for i in range(1, 31)) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.paths.PROJECT_ROOT", project)

    from src.config.instances import count_accounts_in_file, get_max_accounts

    assert count_accounts_in_file(project) == 30
    assert get_max_accounts() == 30


def test_first_drop_returns_ready_unclaimed_when_watch_complete():
    campaign = MagicMock(spec=DropsCampaign)
    done = _make_drop(drop_id="a", name="Drop A", required=30, current=33, claimed=False)
    done.can_earn.return_value = True
    type(done).current_minutes = PropertyMock(return_value=33)
    campaign.drops = [done]

    result = DropsCampaign.first_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is done


def test_first_drop_skips_completed_when_next_needs_time():
    campaign = MagicMock(spec=DropsCampaign)
    done = _make_drop(drop_id="a", name="Drop A", required=30, current=33, claimed=False)
    done.can_earn.return_value = True
    type(done).current_minutes = PropertyMock(return_value=33)
    type(done).remaining_minutes = PropertyMock(return_value=0)
    next_drop = _make_drop(drop_id="b", name="Drop B", required=60, current=5, claimed=False)
    next_drop.can_earn.return_value = True
    type(next_drop).current_minutes = PropertyMock(return_value=5)
    type(next_drop).remaining_minutes = PropertyMock(return_value=55)
    campaign.drops = [done, next_drop]

    result = DropsCampaign.first_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is next_drop


def test_remaining_minutes_never_negative():
    drop = TimedDrop.__new__(TimedDrop)
    drop.required_minutes = 30
    drop.real_current_minutes = 33
    drop.extra_current_minutes = 0
    assert drop.remaining_minutes == 0


def test_first_drop_skips_watch_complete_for_partial_chain_drop():
    """Shared campaign minutes: next drop may be in progress before prior is claimed."""
    campaign = MagicMock(spec=DropsCampaign)
    done = _make_drop(drop_id="a", name="Captured Moments", required=30, current=30, claimed=False)
    done.can_earn.return_value = True
    type(done).current_minutes = PropertyMock(return_value=30)
    type(done).remaining_minutes = PropertyMock(return_value=0)

    nxt = _make_drop(drop_id="b", name="Blooming Spring", required=30, current=21, claimed=False)
    nxt.can_earn.return_value = False
    type(nxt).current_minutes = PropertyMock(return_value=21)
    type(nxt).remaining_minutes = PropertyMock(return_value=9)
    campaign.drops = [done, nxt]

    result = DropsCampaign.first_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is nxt


def test_mining_display_drop_skips_watch_complete():
    campaign = MagicMock()
    done = _make_drop(drop_id="a", name="Captured Moments", required=30, current=30, claimed=False)
    nxt = _make_drop(drop_id="b", name="Blooming Spring", required=30, current=21, claimed=False)
    campaign.progress_drop = nxt

    result = DropsCampaign.mining_display_drop(campaign, done)  # type: ignore[arg-type]
    assert result is nxt


def test_progress_drop_skips_completed_for_owcs_chain():
    """After Time for Waffles completes, bar should show BP Tier Skip in progress."""
    campaign = MagicMock(spec=DropsCampaign)
    waffles = _make_drop(
        drop_id="waffles",
        name="Time for Waffles Icon",
        required=60,
        current=60,
        claimed=False,
    )
    bp = _make_drop(
        drop_id="bp-a",
        name="BP Tier Skip S2.C3.A",
        required=180,
        current=83,
        claimed=False,
        preconditions=["waffles"],
    )
    bp.can_earn.return_value = False
    campaign.drops = [waffles, bp]

    result = DropsCampaign.progress_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is bp


def test_progress_drop_skips_waffles_when_last_in_api_order():
    """Waffles may be last in API order but must not show once watch-complete."""
    campaign = MagicMock(spec=DropsCampaign)
    bp = _make_drop(
        drop_id="bp-a",
        name="BP Tier Skip S2.C3.A",
        required=180,
        current=71,
        claimed=False,
        preconditions=["waffles"],
    )
    shine = _make_drop(
        drop_id="shine",
        name="Time to Shine Name Card",
        required=600,
        current=71,
        claimed=False,
        preconditions=["bp-b"],
    )
    waffles = _make_drop(
        drop_id="waffles",
        name="Time for Waffles Icon",
        required=60,
        current=60,
        claimed=False,
    )
    campaign.drops = [bp, shine, waffles]

    result = DropsCampaign.progress_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is bp
    assert result.name == "BP Tier Skip S2.C3.A"


def test_progress_drop_returns_shine_when_prior_chain_complete():
    campaign = MagicMock(spec=DropsCampaign)
    waffles = _make_drop(
        drop_id="waffles",
        name="Time for Waffles Icon",
        required=60,
        current=60,
        claimed=True,
    )
    bp = _make_drop(
        drop_id="bp-a",
        name="BP Tier Skip S2.C3.A",
        required=180,
        current=180,
        claimed=True,
    )
    shine = _make_drop(
        drop_id="shine",
        name="Time to Shine Name Card",
        required=600,
        current=71,
        claimed=False,
    )
    campaign.drops = [waffles, bp, shine]

    result = DropsCampaign.progress_drop.fget(campaign)  # type: ignore[attr-defined]
    assert result is shine


def test_update_real_minutes_applies_when_preconditions_block_earning(monkeypatch):
    from src.models.drop import TimedDrop
    from src.services import drop_minutes_cache

    drop_minutes_cache._cache.clear()
    drop = TimedDrop.__new__(TimedDrop)
    drop.id = "bp-a"
    drop.name = "BP Tier Skip S2.C3.A"
    drop.required_minutes = 180
    drop.real_current_minutes = 82
    drop.extra_current_minutes = 0
    drop.is_claimed = False
    drop.campaign = MagicMock()
    drop.can_earn = MagicMock(return_value=False)
    drop._on_state_changed = MagicMock()
    drop._is_auto_granted = MagicMock(return_value=False)

    drop._update_real_minutes(1)

    assert drop.real_current_minutes == 83
    drop._on_state_changed.assert_called()


def test_mining_complete_when_all_drops_claimed():
    from types import SimpleNamespace

    from src.core.client import Twitch

    client = Twitch.__new__(Twitch)
    client.settings = SimpleNamespace(games_to_watch=["2XKO"])
    game = SimpleNamespace(name="2XKO")
    drop = SimpleNamespace(is_claimed=True, required_minutes=30, _base_can_earn=lambda: True)
    campaign = SimpleNamespace(
        game=game,
        can_earn_within=lambda _stamp: True,
        drops=[drop],
    )
    client.inventory = [campaign]

    assert client._mining_complete() is True
