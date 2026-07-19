"""Tests for multi-instance auto launcher."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.instance_launcher import load_instances_registry, spawn_sibling_instances


def test_load_instances_registry(tmp_path: Path):
    (tmp_path / "instances.json").write_text(
        json.dumps({"instances": [{"n": 1, "port": 8080}]}),
        encoding="utf-8",
    )
    assert len(load_instances_registry(tmp_path)) == 1


def test_spawn_skips_child_process(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TDM_CHILD", "1")
    monkeypatch.setenv("TDM_PORT", "8080")
    assert spawn_sibling_instances(tmp_path) == []


def test_spawn_skips_non_primary_port(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("TDM_CHILD", raising=False)
    monkeypatch.setenv("TDM_PORT", "8082")
    assert spawn_sibling_instances(tmp_path) == []


def test_spawn_starts_siblings(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("TDM_CHILD", raising=False)
    monkeypatch.setenv("TDM_PORT", "8080")

    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "instances.json").write_text(
        json.dumps(
            {
                "instances": [
                    {"n": 1, "port": 8080, "data_dir": "data", "label": "a1"},
                    {"n": 2, "port": 8082, "data_dir": "data2", "label": "a2"},
                ]
            }
        ),
        encoding="utf-8",
    )

    mock_popen = MagicMock(return_value=MagicMock())
    with patch("src.instance_launcher._is_port_in_use", return_value=False):
        with patch("src.instance_launcher._wait_for_port", return_value=True):
            with patch("src.instance_launcher.subprocess.Popen", mock_popen):
                started = spawn_sibling_instances(tmp_path)

    assert len(started) == 1
    mock_popen.assert_called_once()
    call_env = mock_popen.call_args.kwargs["env"]
    assert call_env["TDM_PORT"] == "8082"
    assert call_env["TDM_CHILD"] == "1"
    assert call_env["TDM_DATA_DIR"].endswith("data2")


def test_spawn_restarts_stale_port(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("TDM_CHILD", raising=False)
    monkeypatch.setenv("TDM_PORT", "8080")
    monkeypatch.setenv("TDM_RESTART_SIBLINGS", "1")

    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "instances.json").write_text(
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

    mock_popen = MagicMock(return_value=MagicMock())
    checks = [True, True, False]

    def port_in_use(port: int) -> bool:
        if checks:
            return checks.pop(0)
        return False

    with patch("src.instance_launcher._is_port_in_use", side_effect=port_in_use):
        with patch("src.instance_launcher._kill_listener_on_port", return_value=True) as kill:
            with patch("src.instance_launcher._wait_for_port", return_value=True):
                with patch("src.instance_launcher.subprocess.Popen", mock_popen):
                    started = spawn_sibling_instances(tmp_path)

    kill.assert_called_once_with(8082)
    assert len(started) == 1
