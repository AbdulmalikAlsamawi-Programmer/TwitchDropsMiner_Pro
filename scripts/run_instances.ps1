# Start one TwitchDropsMiner process per entry in instances.json
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$instancesFile = Join-Path $ProjectRoot "instances.json"
if (-not (Test-Path $instancesFile)) {
    Write-Error "instances.json not found. Run 'python main.py' once to generate it from accounts.txt."
}

$registry = Get-Content $instancesFile -Raw | ConvertFrom-Json
$python = "python"
if (Test-Path (Join-Path $ProjectRoot "env\Scripts\python.exe")) {
    $python = Join-Path $ProjectRoot "env\Scripts\python.exe"
}

Write-Host "Starting $($registry.instances.Count) instance(s) from accounts.txt / instances.json..."
Write-Host ""

foreach ($inst in $registry.instances) {
    $dataPath = Join-Path $ProjectRoot $inst.data_dir
    New-Item -ItemType Directory -Force -Path $dataPath | Out-Null
    $port = [string]$inst.port
    $label = $inst.label
    Write-Host "  Instance $($inst.n): $label on http://localhost:$port/  (data: $($inst.data_dir))"

    $cmd = "set TDM_PORT=$port&& set TDM_DATA_DIR=$dataPath&& set TDM_CHILD=1&& `"$python`" main.py"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmd -WorkingDirectory $ProjectRoot -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "All instances started in the background (no extra windows)."
Write-Host "Open http://localhost:8080/ and use the account tabs to switch (localhost uses direct ports)."
