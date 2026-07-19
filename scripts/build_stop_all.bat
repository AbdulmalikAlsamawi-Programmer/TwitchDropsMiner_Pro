@echo off
cd /d "%~dp0\.."
set "PY=python"
if exist "env\Scripts\python.exe" set "PY=env\Scripts\python.exe"

echo Building stop_all.exe...
"%PY%" -m pip install pyinstaller --quiet
"%PY%" -m PyInstaller stop_all.spec --noconfirm
if not exist "dist\stop_all.exe" (
    echo Build failed.
    pause
    exit /b 1
)

copy /Y "dist\stop_all.exe" "stop_all.exe" >nul
echo.
echo OK: stop_all.exe
echo Double-click stop_all.exe to stop all main.exe processes.
echo.
pause
