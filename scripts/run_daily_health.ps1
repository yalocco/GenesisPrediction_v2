# scripts/run_daily_health.ps1
# Safe wrapper: run the existing daily pipeline, then generate Data Health JSON for GUI.

$ErrorActionPreference = "Stop"

function Get-TodayIso {
  return (Get-Date).ToString("yyyy-MM-dd")
}

Write-Host "=== GenesisPrediction v2: run_daily_health ===" -ForegroundColor Cyan
Write-Host "[1/2] Running existing daily pipeline: scripts/run_daily.ps1" -ForegroundColor Cyan

# Run the existing script in the repo root context
& "$PSScriptRoot\run_daily.ps1"
if ($LASTEXITCODE -ne 0) {
  Write-Host "[ERROR] run_daily.ps1 failed (exit=$LASTEXITCODE). Stop." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "[2/2] Building Data Health JSON" -ForegroundColor Cyan

$today = Get-TodayIso
$py = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
  Write-Host "[ERROR] venv python not found: $py" -ForegroundColor Red
  Write-Host "Hint: create venv or adjust path." -ForegroundColor Yellow
  exit 1
}

# analysis dir should match what app/server.py serves as /analysis/
$analysisDir = "data/world_politics/analysis"

& $py "scripts/build_data_health.py" --analysis-dir $analysisDir --date $today --write-dated
if ($LASTEXITCODE -ne 0) {
  Write-Host "[ERROR] build_data_health.py failed (exit=$LASTEXITCODE)." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "[OK] run_daily_health completed." -ForegroundColor Green
exit 0
