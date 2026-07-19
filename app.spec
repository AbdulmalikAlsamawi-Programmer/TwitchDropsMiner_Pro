# PyInstaller spec — builds dist/main/main.exe (onedir; required for multi-instance spawning)
# Run: pyinstaller app.spec
# Or:  powershell -File scripts/build_exe.ps1

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
root = Path(SPECPATH)

_src_hidden = collect_submodules("src")
_tzdata_datas = collect_data_files("tzdata")

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "web"), "web"),
        (str(root / "lang"), "lang"),
        (str(root / "owleague.store.png"), "."),
    ]
    + _tzdata_datas,
    hiddenimports=_src_hidden
    + [
        "src.__main__",
        "truststore",
        "tzdata",
        "tzdata.zoneinfo",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "engineio.async_drivers.aiohttp",
        "engineio.async_drivers.asgi",
        "socketio.async_server",
        "socketio.async_client",
        "multipart",
        "multipart.multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(root / "pyi_rth_tzdata.py")],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="main",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="main",
)
