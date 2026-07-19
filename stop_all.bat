@echo off
cd /d "%~dp0"

if exist "%~dp0stop_all.exe" (
    "%~dp0stop_all.exe"
    exit /b 0
)

set "TASKKILL=%SystemRoot%\System32\taskkill.exe"
if not exist "%TASKKILL%" (
    echo ERROR: stop_all.exe missing and taskkill not found.
    echo Run scripts\build_stop_all.bat to build stop_all.exe
    pause
    exit /b 1
)

echo Stopping TwitchDropsMiner (main.exe)...
"%TASKKILL%" /F /IM main.exe >nul 2>&1
if errorlevel 1 (
    echo No main.exe processes were running.
) else (
    echo Done. All main.exe processes stopped.
)
echo.
pause
