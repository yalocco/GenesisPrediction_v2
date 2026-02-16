# scripts/run_morning_ritual.ps1
# Morning Ritual (single entrypoint)
# Goal: run ONLY this script every morning.
# - run_daily_with_publish (analyzer + news publish + ensure html + fx overlay + summary normalize)
# - fx rates (optional but recommended)
# - fx inputs
# - fx overlay (again, after rates/inputs, to refresh overlays)
# - build_data_health
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-16
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Guard

[CmdletBinding()]
param(
  [string]$Date,
  [switch]$Guard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") }

function Run-Step {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][ScriptBlock]$Action
  )
  Write-Host ""
  Write-Host ("[{0}] === {1} ===" -f (NowStamp), $Title)
  & $Action
  if ($LASTEXITCODE -ne 0) {
    throw ("[ERROR] step failed (exit={0}): {1}" -f $LASTEXITCODE, $Title)
  }
}

$ROOT = (Resolve-Path ".").Path

if ([string]::IsNullOrWhiteSpace($Date)) {
  # Keep consistent with existing scripts: default UTC date
  $Date = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
  $dateNote = " (default=UTC today)"
} else {
  $dateNote = ""
}

$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

Write-Host ""
Write-Host "Morning Ritual (single entrypoint)"
Write-Host ("ROOT : {0}" -f $ROOT)
Write-Host ("DATE : {0}{1}" -f $Date, $dateNote)
Write-Host ("GUARD: {0}" -f ($(if ($Guard) { "ON" } else { "OFF" })))

# 1) Core pipeline + publish + ensure + fx overlay + summary normalize (+ optional guard)
Run-Step -Title "1) run_daily_with_publish" -Action {
  if ($Guard) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_with_publish.ps1") -Date $Date -Guard
  } else {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_with_publish.ps1") -Date $Date
  }
}

# 2) FX rates (recommended; keeps dashboard less stale)
Run-Step -Title "2) FX rates" -Action {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_rates.ps1")
}

# 3) FX inputs (uses latest decision logic)
Run-Step -Title "3) FX inputs" -Action {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1")
}

# 4) FX overlay again (after rates/inputs) to maximize freshness
Run-Step -Title "4) FX overlay (refresh)" -Action {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1")
}

# 5) Data Health build
Run-Step -Title "5) build_data_health" -Action {
  & $PY (Join-Path $ROOT "scripts\build_data_health.py") --date $Date
}

Write-Host ""
Write-Host ("[{0}] DONE Morning Ritual" -f (NowStamp))
exit 0
