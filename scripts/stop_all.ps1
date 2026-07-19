# Stop all TwitchDropsMiner main.exe processes (primary + sibling accounts).
# Prefer stop_all.bat in project root if PowerShell is not on PATH.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$procs = Get-CimInstance Win32_Process -Filter "Name='main.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and ($_.ExecutablePath -like "$Root*") }

if (-not $procs) {
    # Fallback: any main.exe (only use this app named main.exe in the folder)
    $procs = Get-Process -Name main -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "$Root*" }
}

if (-not $procs) {
    Write-Host "No main.exe processes found for: $Root"
    exit 0
}

$count = @($procs).Count
foreach ($p in $procs) {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Write-Host "Stopped $count main.exe process(es)."
