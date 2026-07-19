# Build main.exe and deploy to project root:
#   main.exe      (launcher)
#   _internal/    (bundled Python + web + lang)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$venvPython = Join-Path $Root "env\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

Write-Host "Installing PyInstaller if needed..."
& $venvPython -m pip install pyinstaller --quiet

Write-Host "Building main.exe from main.py..."
& $venvPython -m PyInstaller app.spec --noconfirm

$builtExe = Join-Path $Root "dist\main\main.exe"
$builtInternal = Join-Path $Root "dist\main\_internal"
if (-not (Test-Path $builtExe)) {
    Write-Error "Build failed — dist\main\main.exe not found"
}

$rootExe = Join-Path $Root "main.exe"
$rootInternal = Join-Path $Root "_internal"

Write-Host "Deploying to project root..."
Copy-Item -Path $builtExe -Destination $rootExe -Force

if (Test-Path $rootInternal) {
    Remove-Item -Path $rootInternal -Recurse -Force
    if (Test-Path $rootInternal) {
        Write-Error "Could not remove old _internal — stop main.exe first, then rebuild."
    }
}
Copy-Item -Path $builtInternal -Destination $rootInternal -Recurse -Force

$viennaTz = Join-Path $rootInternal "tzdata\zoneinfo\Europe\Vienna"
$webIndex = Join-Path $rootInternal "web\index.html"
if (-not (Test-Path $viennaTz)) {
    Write-Error "Deploy incomplete — missing $viennaTz (nested _internal copy?)"
}
if (-not (Test-Path $webIndex)) {
    Write-Error "Deploy incomplete — missing $webIndex"
}

Write-Host ""
Write-Host "Build OK — ready to run from project root:"
Write-Host "  $rootExe"
Write-Host "  $rootInternal\"
Write-Host ""
Write-Host "Keep accounts.txt in the same folder as main.exe."
Write-Host "Run: .\main.exe   or double-click main.exe"
Write-Host "Web UI: http://127.0.0.1:8080"
