"""Tests for accounts.txt loading and cookie bootstrap."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config.accounts_loader import (
    AccountEntry,
    bootstrap_accounts,
    build_cookie_jar,
    parse_accounts_line,
    parse_accounts_file,
    write_account_cookies,
)


def test_parse_accounts_line_valid():
    entry = parse_accounts_line("user1:pass1:tokenabc:12345:2024-05")
    assert entry == AccountEntry(
        username="user1", password="pass1", token="tokenabc", user_id="12345"
    )


def test_parse_accounts_line_skips_comments_and_blanks():
    assert parse_accounts_line("") is None
    assert parse_accounts_line("# comment") is None
    assert parse_accounts_line("too:few:fields") is None


def test_parse_accounts_file(tmp_path: Path):
    path = tmp_path / "accounts.txt"
    path.write_text(
        "# header\n"
        "alice:pw1:tok1:111\n"
        "bob:pw2:tok2:222:extra\n",
        encoding="utf-8",
    )
    accounts = parse_accounts_file(path)
    assert len(accounts) == 2
    assert accounts[0].username == "alice"
    assert accounts[1].token == "tok2"


def test_build_cookie_jar_contains_auth_token():
    jar = build_cookie_jar("mytoken", "999", "device123")
    www = jar["www.twitch.tv|"]
    assert www["auth-token"]["value"] == "mytoken"
    assert www["persistent"]["value"] == "999"
    assert www["unique_id"]["value"] == "device123"


def test_write_account_cookies_preserves_device_id(tmp_path: Path):
    account_dir = tmp_path / "accounts" / "alice"
    write_account_cookies(account_dir, "tok1", "111")
    first = json.loads((account_dir / "cookies.jar").read_text(encoding="utf-8"))
    device = first["www.twitch.tv|"]["unique_id"]["value"]

    write_account_cookies(account_dir, "tok2", "111")
    second = json.loads((account_dir / "cookies.jar").read_text(encoding="utf-8"))
    assert second["www.twitch.tv|"]["auth-token"]["value"] == "tok2"
    assert second["www.twitch.tv|"]["unique_id"]["value"] == device


def test_bootstrap_accounts_sets_active_and_cookies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project = tmp_path / "proj"
    project.mkdir()
    data_dir = project / "data"
    data_dir.mkdir()

    (project / "accounts.txt").write_text(
        "acc1:pw1:token1:1001\nacc2:pw2:token2:1002\n",
        encoding="utf-8",
    )
    (project / "instances.json").write_text(
        json.dumps(
            {
                "instances": [
                    {"n": 1, "port": 8080, "data_dir": "data", "pm2_name": "t1", "label": "A1"},
                    {"n": 2, "port": 8082, "data_dir": "data2", "pm2_name": "t2", "label": "A2"},
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TDM_DATA_DIR", str(data_dir))
    monkeypatch.setenv("TDM_PORT", "8082")
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    loaded = bootstrap_accounts()
    assert len(loaded) == 2
    assert (data_dir / "accounts" / "acc2" / "cookies.jar").is_file()

    cfg = json.loads((data_dir / "web_config.json").read_text(encoding="utf-8"))
    assert cfg["active_account"] == "acc2"

    instances = json.loads((project / "instances.json").read_text(encoding="utf-8"))
    assert len(instances["instances"]) == 2
    assert instances["instances"][0]["label"] == "acc1"
    assert instances["instances"][1]["label"] == "acc2"
    assert instances["instances"][1]["port"] == 8082
    assert instances["instances"][1]["data_dir"] == "data2"


def test_sync_instances_registry_creates_all_accounts(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    accounts_path = project / "accounts.txt"
    lines = [f"a{i}:p:t{i}:{i}\n" for i in range(1, 101)]
    accounts_path.write_text("".join(lines), encoding="utf-8")
    from src.config.accounts_loader import _sync_instances_registry, parse_accounts_file
    from src.config.instances import DEFAULT_MAX_ACCOUNTS, instance_port

    accounts = parse_accounts_file(accounts_path)
    _sync_instances_registry(project, accounts)
    data = json.loads((project / "instances.json").read_text(encoding="utf-8"))
    assert len(data["instances"]) == DEFAULT_MAX_ACCOUNTS
    assert data["instances"][0]["port"] == 8080
    assert data["instances"][-1]["n"] == DEFAULT_MAX_ACCOUNTS
    assert data["instances"][-1]["port"] == instance_port(DEFAULT_MAX_ACCOUNTS)


def test_get_account_for_instance_by_active_account(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    data_dir = project / "data"
    data_dir.mkdir()
    (project / "accounts.txt").write_text("alice:p:tok1:1\nbob:p:tok2:2\n", encoding="utf-8")
    (data_dir / "web_config.json").write_text(
        json.dumps({"active_account": "bob"}), encoding="utf-8"
    )
    monkeypatch.setenv("TDM_DATA_DIR", str(data_dir))
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.config.accounts_loader import get_account_for_instance

    account = get_account_for_instance(project)
    assert account is not None
    assert account.username == "bob"
    assert account.token == "tok2"


def test_save_accounts_content_writes_file_and_syncs(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    data_dir = project / "data"
    data_dir.mkdir()
    monkeypatch.setenv("TDM_DATA_DIR", str(data_dir))
    monkeypatch.setenv("TDM_PORT", "8080")
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    content = "# my accounts\nalice:pw1:tok1:1001\nbob:pw2:tok2:1002\n"
    accounts, warnings = __import__(
        "src.config.accounts_loader", fromlist=["save_accounts_content"]
    ).save_accounts_content(content)

    assert len(accounts) == 2
    assert warnings == []
    assert (project / "accounts.txt").is_file()
    instances = json.loads((project / "instances.json").read_text(encoding="utf-8"))
    assert len(instances["instances"]) == 2
    assert (data_dir / "accounts" / "alice" / "cookies.jar").is_file()


def test_save_accounts_content_rejects_empty(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.config.accounts_loader import save_accounts_content

    with pytest.raises(ValueError, match="No valid accounts"):
        save_accounts_content("bad line\n# comment only\n")


def test_has_accounts(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.config.accounts_loader import has_accounts

    assert has_accounts(project) is False
    (project / "accounts.txt").write_text("u:p:t:1\n", encoding="utf-8")
    assert has_accounts(project) is True


def test_reset_instance_data_preserves_settings(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "accounts.txt").write_text("u:p:t:1\n", encoding="utf-8")
    (project / "instances.json").write_text(
        json.dumps(
            {
                "instances": [
                    {"n": 1, "port": 8080, "data_dir": "data"},
                    {"n": 2, "port": 8082, "data_dir": "data2"},
                ]
            }
        ),
        encoding="utf-8",
    )
    data = project / "data"
    data.mkdir()
    settings = {"language": "العربية", "games_to_watch": ["REMATCH"]}
    (data / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    (data / "cookies.jar").write_text("{}", encoding="utf-8")
    data2 = project / "data2"
    data2.mkdir()
    (data2 / "drop_minutes_cache.json").write_text('{"x": 30}', encoding="utf-8")

    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)
    monkeypatch.setattr("src.config.SETTINGS_PATH", data / "settings.json")
    monkeypatch.setenv("TDM_PORT", "8080")
    monkeypatch.delenv("TDM_CHILD", raising=False)

    from src.config.accounts_loader import reset_instance_data_on_startup

    count = reset_instance_data_on_startup(project)
    assert count == 2
    assert not (data2 / "drop_minutes_cache.json").exists()
    restored = json.loads((data / "settings.json").read_text(encoding="utf-8"))
    assert restored["language"] == "العربية"
    assert restored["games_to_watch"] == ["REMATCH"]


def test_sync_setup_complete_all_instances(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "accounts.txt").write_text("u:p:t:1\n", encoding="utf-8")
    (project / "instances.json").write_text(
        json.dumps(
            {
                "instances": [
                    {"n": 1, "port": 8080, "data_dir": "data"},
                    {"n": 2, "port": 8082, "data_dir": "data2"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.config.accounts_loader._project_root", lambda: project)

    from src.config.accounts_loader import sync_setup_complete_all_instances

    sync_setup_complete_all_instances(project)
    for name in ("data", "data2"):
        cfg = json.loads((project / name / "web_config.json").read_text(encoding="utf-8"))
        assert cfg["setup_done"] is True
