"""Web/lang paths prefer project root over bundled _internal."""

from __future__ import annotations

from pathlib import Path


def test_web_dir_prefers_project_root(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    bundle = tmp_path / "bundle"
    (project / "web").mkdir(parents=True)
    (project / "web" / "index.html").write_text("<html>Owleague</html>", encoding="utf-8")
    (bundle / "web").mkdir(parents=True)
    (bundle / "web" / "index.html").write_text("<html>Old</html>", encoding="utf-8")

    monkeypatch.setattr("src.config.paths.PROJECT_ROOT", project)
    monkeypatch.setattr("src.config.paths.BUNDLE_ROOT", bundle)
    monkeypatch.setattr("src.config.paths.WEB_DIR", project / "web")

    from src.config.paths import _prefer_project_dir

    assert _prefer_project_dir("web") == project / "web"
