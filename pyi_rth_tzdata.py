"""PyInstaller runtime hook: configure TZPATH before zoneinfo is used."""
import os
import sys

if getattr(sys, "frozen", False):
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for rel in ("tzdata/zoneinfo", "zoneinfo"):
            path = os.path.join(meipass, *rel.split("/"))
            if os.path.isdir(path):
                os.environ["TZPATH"] = path
                break
