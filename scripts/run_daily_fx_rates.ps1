# scripts/run_daily_fx_rates.ps1
# FX Rates Runner (API guarded)
#
# Purpose:
# - Call fx_materialize_rates.py with explicit pairs
# - Designed to be called ONLY from run_morning_ritual.ps1
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_rates.ps1

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { (Get-Date).ToString("HH:mm:ss") }

$ROOT = (Resolve-Path ".").Path
$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

$scriptPath = Join-Path $ROOT "scripts\fx_materialize_rates.py"

Write-Host ("[{0}] START FX rates strict=False" -f (NowStamp))

# --- Define pairs here (single source of truth) ---
$pairs = @(
  "usdthb",
  "usdjpy"
)

foreach ($pair in $pairs) {
    Write-Host ("[{0}] PY  fx_materialize_rates.py --pair {1}" -f (NowStamp), $pair)

    & $PY $scriptPath --pair $pair
    $code = $LASTEXITCODE

    if ($code -ne 0) {
        Write-Host ("[{0}] ERROR Python failed (fx_materialize_rates.py --pair {1}) exit={2}" -f (NowStamp), $pair, $code)
        exit 1
    }
}

Write-Host ("[{0}] DONE FX rates" -f (NowStamp))
exit 0