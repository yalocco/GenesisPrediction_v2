# scripts/run_daily_fx_rates.ps1
# FX Rates Runner (API guarded)
#
# Purpose:
# - Call fx_materialize_rates.py with explicit pairs
# - Designed to be called ONLY from run_morning_ritual.ps1
# - Add deterministic pair-to-pair pacing to avoid API quota/pacing collisions
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_rates.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_rates.ps1 -CooldownSeconds 75

[CmdletBinding()]
param(
    [int]$CooldownSeconds = 75
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { (Get-Date).ToString("HH:mm:ss") }

$ROOT = (Resolve-Path ".").Path
$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

$scriptPath = Join-Path $ROOT "scripts/fx_materialize_rates.py"

Write-Host ("[{0}] START FX rates strict=False cooldown_seconds={1}" -f (NowStamp), $CooldownSeconds)

# --- Define pairs here (single source of truth) ---
$pairs = @(
  "usdthb",
  "usdjpy"
)

for ($i = 0; $i -lt $pairs.Count; $i++) {
    $pair = $pairs[$i]

    Write-Host ("[{0}] PY  fx_materialize_rates.py --pair {1}" -f (NowStamp), $pair)

    $fxOutput = & $PY $scriptPath --pair $pair 2>&1
    $code = $LASTEXITCODE

    foreach ($line in $fxOutput) {
        Write-Host $line
    }

    if ($code -ne 0) {
        Write-Host ("[{0}] ERROR Python failed (fx_materialize_rates.py --pair {1}) exit={2}" -f (NowStamp), $pair, $code)
        exit 1
    }

    $outputText = ($fxOutput | Out-String)
    $skippedOnlineBecauseAlreadyAttempted = ($outputText -match "skip online \(already_attempted_today\(ok\)\)")

    if ($i -lt ($pairs.Count - 1)) {
        if ($skippedOnlineBecauseAlreadyAttempted) {
            Write-Host ("[{0}] SKIP FX pair cooldown because online fetch was already attempted today for {1}" -f (NowStamp), $pair)
        } else {
            Write-Host ("[{0}] WAIT FX pair cooldown seconds={1}" -f (NowStamp), $CooldownSeconds)
            Start-Sleep -Seconds $CooldownSeconds
        }
    }
}

Write-Host ("[{0}] DONE FX rates" -f (NowStamp))
exit 0
