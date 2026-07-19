"""Tests for multi-instance log prefixing."""

from __future__ import annotations

import logging

from src.utils.log_context import InstanceContextFilter, set_instance_login


def test_instance_context_filter_prefixes_message_once(monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8086")
    set_instance_login("testuser")

    filt = InstanceContextFilter()
    record = logging.LogRecord(
        name="TwitchDrops",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Watching: channel",
        args=(),
        exc_info=None,
    )
    assert filt.filter(record) is True
    assert record.msg == "[8086:testuser] Watching: channel"
    assert filt.filter(record) is True
    assert record.msg == "[8086:testuser] Watching: channel"


def test_instance_context_filter_prefixes_message(monkeypatch):
    monkeypatch.setenv("TDM_PORT", "8086")
    set_instance_login("testuser")

    record = logging.LogRecord(
        name="TwitchDrops",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Watching: channel",
        args=(),
        exc_info=None,
    )
    assert InstanceContextFilter().filter(record) is True
    assert record.msg == "[8086:testuser] Watching: channel"
