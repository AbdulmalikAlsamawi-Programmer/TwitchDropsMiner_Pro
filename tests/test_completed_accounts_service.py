"""Tests for completed account archiving per target game."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

from src.services.completed_accounts_service import (
    CompletedAccountsService,
    append_account_line,
    complete_file_for_game,
    drop_mining_done,
    is_game_mining_complete,
    safe_game_filename,
)


def _drop(*, claimed=False, required=60, current=0, can_earn=True):
    drop = MagicMock()
    drop.is_claimed = claimed
    drop.required_minutes = required
    type(drop).current_minutes = PropertyMock(return_value=current)
    drop._base_can_earn.return_value = can_earn
    return drop


def _campaign(game_name: str, drops: list, *, can_earn_within=True):
    campaign = MagicMock()
    campaign.game.name = game_name
    campaign.can_earn_within.return_value = can_earn_within
    campaign.drops = drops
    return campaign


def test_drop_mining_done():
    assert drop_mining_done(_drop(claimed=True)) is True
    assert drop_mining_done(_drop(required=60, current=60)) is True
    assert drop_mining_done(_drop(required=60, current=30)) is False


def test_is_game_mining_complete():
    inventory = [
        _campaign(
            "Overwatch",
            [
                _drop(claimed=True, required=60, current=60),
                _drop(claimed=False, required=180, current=180),
            ],
        )
    ]
    assert is_game_mining_complete(inventory, "Overwatch") is True
    assert is_game_mining_complete(inventory, "League of Legends") is False


def test_is_game_mining_complete_false_when_drop_remaining():
    inventory = [
        _campaign(
            "Overwatch",
            [
                _drop(claimed=True, required=60, current=60),
                _drop(required=180, current=90),
            ],
        )
    ]
    assert is_game_mining_complete(inventory, "Overwatch") is False


def test_append_account_line_deduplicates(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    line = "alice:p:t1:1"
    assert append_account_line("Overwatch", line, project_root=root) is True
    assert append_account_line("Overwatch", line, project_root=root) is False
    path = complete_file_for_game("Overwatch", root)
    assert path.read_text(encoding="utf-8") == "alice:p:t1:1\n"


def test_safe_game_filename():
    assert safe_game_filename("Overwatch") == "Overwatch"
    assert safe_game_filename("League of Legends") == "League of Legends"
    assert safe_game_filename("Bad/Name") == "Bad_Name"


def test_completed_accounts_service_records_finished_game(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "accounts.txt").write_text("alice:p:t1:1\n", encoding="utf-8")

    monkeypatch.setattr("src.config.paths.PROJECT_ROOT", root)
    monkeypatch.setattr("src.services.completed_accounts_service.PROJECT_ROOT", root)

    from src.config.accounts_loader import AccountEntry

    account = AccountEntry("alice", "p", "t1", "1")
    monkeypatch.setattr(
        "src.services.completed_accounts_service.get_account_for_instance",
        lambda project_root=None: account,
    )

    twitch = MagicMock()
    twitch.settings.games_to_watch = ["Overwatch"]
    twitch.inventory = [
        _campaign("Overwatch", [_drop(claimed=True, required=60, current=60)])
    ]
    twitch.print = MagicMock()

    recorded = CompletedAccountsService(twitch).check_and_record()

    assert recorded == ["Overwatch"]
    assert complete_file_for_game("Overwatch", root).read_text(encoding="utf-8") == "alice:p:t1:1\n"
