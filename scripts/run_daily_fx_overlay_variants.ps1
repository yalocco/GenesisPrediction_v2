# scripts/run_daily_fx_overlay_variants.ps1
# Build FX overlay PNG variants (latest_jpythb/usdjpy/usdthb) into analysis/fx/
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_overlay_variants.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_overlay_variants.ps1 -Date 2026-02-05
#
# Notes:
# - This runner calls: scripts/build_fx_overlay_variants.py
# - It should be executed AFTER your FX data materialization / overlay generation steps.

param(
  [Parameter(Mandatory=$false)]
  [string]$Date = ""
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  # This script lives in <repo>\scripts\
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$ROOT = Get-RepoRoot

Write-Host ""
Write-Host "GenesisPrediction v2 - run_daily_fx_overlay_variants"
Write-Host ("ROOT : {0}" -f $ROOT)
if ($Date -ne "") {
  Write-Host ("DATE : {0}" -f $Date)
} else {
  Write-Host "DATE : (infer from CSV last date)"
}
Write-Host ""

$py = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  throw "python not found: $py"
}

$script = Join-Path $ROOT "scripts\build_fx_overlay_variants.py"
if (-not (Test-Path $script)) {
  throw "script not found: $script"
}

$cmd = @($py, $script)
if ($Date -ne "") {
  $cmd += @("--date", $Date)
}

Write-Host ("CMD: {0}" -f ($cmd -join " "))
& $py $script @(
  $(if ($Date -ne "") { "--date"; $Date } else { })
)

Write-Host ""
Write-Host "[OK] done: build fx overlay variants"