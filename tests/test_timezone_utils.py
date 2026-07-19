"""Tests for Vienna timezone helpers (PyInstaller / Windows zoneinfo)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def test_vienna_today_returns_iso_date():
    from src.utils.timezone_utils import vienna_today

    result = vienna_today()
    assert len(result) == 10
    assert result[4] == "-" and result[7] == "-"


def test_configure_tzdata_for_frozen_sets_tzpath(tmp_path, monkeypatch):
    zi = tmp_path / "tzdata" / "zoneinfo"
    zi.mkdir(parents=True)

    fake_sys = type(
        "FakeSys",
        (),
        {"frozen": True, "_MEIPASS": str(tmp_path)},
    )()
    monkeypatch.setattr("src.utils.timezone_utils.sys", fake_sys)
    monkeypatch.delenv("TZPATH", raising=False)

    from src.utils.timezone_utils import configure_tzdata_for_frozen

    configure_tzdata_for_frozen()
    assert os.environ.get("TZPATH") == str(zi)


def test_vienna_zone_file_finds_bundled_path(tmp_path, monkeypatch):
    vienna = tmp_path / "tzdata" / "zoneinfo" / "Europe" / "Vienna"
    vienna.parent.mkdir(parents=True)
    vienna.write_bytes(b"TZif")

    fake_sys = type(
        "FakeSys",
        (),
        {"frozen": True, "_MEIPASS": str(tmp_path)},
    )()
    monkeypatch.setattr("src.utils.timezone_utils.sys", fake_sys)
    monkeypatch.delenv("TZPATH", raising=False)

    from src.utils.timezone_utils import _vienna_zone_file, get_vienna_tz

    get_vienna_tz.cache_clear()

    assert Path(_vienna_zone_file()) == vienna


def test_get_vienna_tz_does_not_raise():
    from src.utils.timezone_utils import get_vienna_tz

    tz = get_vienna_tz()
    assert tz is not None
    assert str(tz) in ("Europe/Vienna", "UTC")
