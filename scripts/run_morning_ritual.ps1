# scripts/run_morning_ritual.ps1
# Morning Ritual - Single Entry Point
#
# Purpose:
# - Run daily publish pipeline
# - Run FX pipeline (ONLY here touches FX APIs)
# - Build data health
#
# Design Rule:
# - FX API calls are centralized here.
# - run_daily_with_publish.ps1 MUST NOT call FX.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-22

[CmdletBinding()]
param(
  [string]$Date
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") }

function Run-Step {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][string]$CommandLine
  )
  Write-Host ""
  Write-Host ("[{0}] === {1} ===" -f (NowStamp), $Title)
  Write-Host ("CMD: {0}" -f $CommandLine)

  & powershell -NoProfile -ExecutionPolicy Bypass -Command $CommandLine
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    throw ("[ERROR] step failed (exit={0}): {1}" -f $code, $Title)
  }
}

$ROOT = (Resolve-Path ".").Path

if ([string]::IsNullOrWhiteSpace($Date)) {
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

# -------------------------------------------------------
# 1) Publish / Analyzer (NO FX here)
# -------------------------------------------------------
$runDaily = Join-Path $ROOT "scripts\run_daily_with_publish.ps1"
Run-Step `
  -Title "1) run_daily_with_publish" `
  -CommandLine "cd `"$ROOT`"; powershell -ExecutionPolicy Bypass -File `"$runDaily`" -Date $Date"

# -------------------------------------------------------
# 2) FX Pipeline (ONLY HERE touches API)
# -------------------------------------------------------
$fxRates = Join-Path $ROOT "scripts\run_daily_fx_rates.ps1"
$fxInputs = Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1"
$fxOverlay = Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1"

Run-Step `
  -Title "2-1) FX Rates (API guarded)" `
  -CommandLine "cd `"$ROOT`"; powershell -ExecutionPolicy Bypass -File `"$fxRates`""

Run-Step `
  -Title "2-2) FX Inputs" `
  -CommandLine "cd `"$ROOT`"; powershell -ExecutionPolicy Bypass -File `"$fxInputs`""

Run-Step `
  -Title "2-3) FX Overlay" `
  -CommandLine "cd `"$ROOT`"; powershell -ExecutionPolicy Bypass -File `"$fxOverlay`""

# -------------------------------------------------------
# 3) Data Health
# -------------------------------------------------------
$healthPy = Join-Path $ROOT "scripts\build_data_health.py"

Run-Step `
  -Title "3) Build Data Health" `
  -CommandLine "cd `"$ROOT`"; `"$PY`" `"$healthPy`" --date $Date"

Write-Host ""
Write-Host ("[{0}] DONE Morning Ritual" -f (NowStamp))
exit 0