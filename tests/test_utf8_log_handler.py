"""Tests for UTF-8 console logging handler."""

from __future__ import annotations

import io
import logging

from src.utils.log_context import UTF8StreamHandler


def test_utf8_stream_handler_replaces_unencodable_chars():
    stream = io.TextIOWrapper(io.BytesIO(), encoding="ascii", errors="strict")
    handler = UTF8StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="العربية watching",
        args=(),
        exc_info=None,
    )
    handler.emit(record)
    stream.flush()
    stream.buffer.seek(0)
    output = stream.buffer.read().decode("ascii", errors="replace")
    assert "watching" in output
