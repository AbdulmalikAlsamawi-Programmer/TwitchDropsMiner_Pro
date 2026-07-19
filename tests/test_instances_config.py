"""Tests for multi-instance scaling configuration."""

from __future__ import annotations

import json

from src.config.instances import (
    ABSOLUTE_MAX_ACCOUNTS,
    DEFAULT_MAX_ACCOUNTS,
    clamp_max_accounts,
    get_max_accounts,
    instance_data_dir_name,
    instance_n_from_port,
    instance_port,
)


def test_default_max_accounts_is_100():
    assert DEFAULT_MAX_ACCOUNTS == 100


def test_get_max_accounts_from_settings(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "settings.json").write_text(json.dumps({"max_accounts": 25}), encoding="utf-8")
    monkeypatch.setattr("src.config.instances._shared_settings_path", lambda: data_dir / "settings.json")
    monkeypatch.setattr("src.config.instances.count_accounts_in_file", lambda project_root=None: 0)
    assert get_max_accounts() == 25


def test_get_max_accounts_clamps_high(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "settings.json").write_text(json.dumps({"max_accounts": 9999}), encoding="utf-8")
    monkeypatch.setattr("src.config.instances._shared_settings_path", lambda: data_dir / "settings.json")
    monkeypatch.setattr("src.config.instances.count_accounts_in_file", lambda project_root=None: 0)
    assert get_max_accounts() == ABSOLUTE_MAX_ACCOUNTS


def test_instance_port_scaling():
    assert instance_port(1) == 8080
    assert instance_port(2) == 8082
    assert instance_port(100) == 8278


def test_instance_n_from_port():
    assert instance_n_from_port(8080) == 1
    assert instance_n_from_port(8278) == 100


def test_instance_data_dir_names():
    assert instance_data_dir_name(1) == "data"
    assert instance_data_dir_name(100) == "data100"


def test_clamp_max_accounts():
    assert clamp_max_accounts(0) == 1
    assert clamp_max_accounts(50) == 50
    assert clamp_max_accounts(9999) == ABSOLUTE_MAX_ACCOUNTS
