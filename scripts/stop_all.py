#!/usr/bin/env python3
"""Stop all TwitchDropsMiner processes (works when taskkill is not on PATH)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SYSTEM = Path(os.environ.get("SystemRoot", r"C:\Windows"))
TASKKILL = SYSTEM / "System32" / "taskkill.exe"
CREATE_NO_WINDOW = 0x08000000


def _pause() -> None:
    if not sys.stdin or not sys.stdin.isatty():
        return
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def _kill_main_exe() -> int:
    if not TASKKILL.is_file():
        print(f"ERROR: taskkill not found: {TASKKILL}")
        return 1
    result = subprocess.run(
        [str(TASKKILL), "/F", "/IM", "main.exe"],
        capture_output=True,
        text=True,
        errors="replace",
        creationflags=CREATE_NO_WINDOW,
    )
    if result.returncode == 0:
        lines = [ln for ln in result.stdout.splitlines() if "SUCCESS:" in ln]
        count = len(lines)
        print(f"Stopped {count} main.exe process(es)." if count else "Stopped main.exe processes.")
        return 0
    if result.returncode == 128:
        print("No main.exe processes were running.")
        return 0
    print(result.stderr.strip() or result.stdout.strip() or f"taskkill failed ({result.returncode})")
    return result.returncode


def main() -> int:
    code = _kill_main_exe()
    _pause()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
