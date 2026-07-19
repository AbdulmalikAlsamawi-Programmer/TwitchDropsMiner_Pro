"""Tests for /api/instances registry path (frozen exe must use PROJECT_ROOT)."""

from __future__ import annotations

import json

from src.config.paths import PROJECT_ROOT


def test_instances_file_is_under_project_root():
    from src.web import app as web_app

    assert web_app._INSTANCES_FILE == PROJECT_ROOT / "instances.json"


def test_load_instances_registry_from_project_root(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    instances = {
        "instances": [
            {"n": 1, "port": 8080, "data_dir": "data", "label": "a1"},
            {"n": 2, "port": 8082, "data_dir": "data2", "label": "a2"},
            {"n": 3, "port": 8084, "data_dir": "data3", "label": "a3"},
        ]
    }
    (project / "instances.json").write_text(json.dumps(instances), encoding="utf-8")
    monkeypatch.setattr("src.config.paths.PROJECT_ROOT", project)
    monkeypatch.setattr("src.web.app.PROJECT_ROOT", project)
    monkeypatch.setattr("src.web.app._INSTANCES_FILE", project / "instances.json")

    from src.web.app import _load_instances_registry

    loaded = _load_instances_registry()
    assert len(loaded["instances"]) == 3
