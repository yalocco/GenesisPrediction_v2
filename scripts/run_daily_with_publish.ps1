# scripts/run_daily_with_publish.ps1
# GenesisPrediction v2 - run_daily_with_publish
# - Runs analyzer
# - Publishes daily_news_latest (for sentiment pipeline) WITHOUT interactive prompts
# - Optional: run guard after publish
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1 -Date 2026-02-15
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1 -Guard
#
# Notes:
# - DATE default is UTC today (to match existing behavior/logs)
# - publish_daily_news_latest is executed via Python script:
#     scripts/publish_daily_news_latest.py --date YYYY-MM-DD
#   so it never prompts "Date:".

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
    [Parameter(Mandatory=$true)][string]$CommandLine
  )
  Write-Host ""
  Write-Host ("[{0}] === {1} ===" -f (NowStamp), $Title)
  Write-Host ("CMD: {0}" -f $CommandLine)

  # Use powershell invocation so quoting stays consistent
  & powershell -NoProfile -ExecutionPolicy Bypass -Command $CommandLine
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    throw ("[ERROR] step failed (exit={0}): {1}" -f $code, $Title)
  }
}

# ----------------------------
# Context
# ----------------------------
$ROOT = (Resolve-Path ".").Path

# Match previous log line: "DATE : YYYY-MM-DD (default=UTC today)"
if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
  $dateNote = " (default=UTC today)"
} else {
  $dateNote = ""
}

# Prefer venv python if exists
$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) {
  # fallback
  $PY = "python"
}

Write-Host ""
Write-Host "GenesisPrediction v2 - run_daily_with_publish"
Write-Host ("ROOT : {0}" -f $ROOT)
Write-Host ("DATE : {0}{1}" -f $Date, $dateNote)
Write-Host ("GUARD: {0}" -f ($(if ($Guard) { "ON" } else { "OFF" })))

# ----------------------------
# 1) Analyzer
# ----------------------------
Run-Step `
  -Title "1) Analyzer (docker compose run --rm analyzer)" `
  -CommandLine "cd `"$ROOT`"; docker compose run --rm analyzer"

# ----------------------------
# 2) Publish daily_news_latest (for sentiment pipeline)
#    IMPORTANT: call PY script with --date to avoid interactive prompts
# ----------------------------
$publishPy = Join-Path $ROOT "scripts\publish_daily_news_latest.py"
if (-not (Test-Path $publishPy)) {
  throw ("[ERROR] missing file: {0}" -f $publishPy)
}

Run-Step `
  -Title "2) Publish daily_news_latest (for sentiment pipeline)" `
  -CommandLine "cd `"$ROOT`"; `"$PY`" `"$publishPy`" --date $Date"

# ----------------------------
# 3) Optional Guard
# ----------------------------
if ($Guard) {
  $guardPs1 = Join-Path $ROOT "scripts\run_daily_guard.ps1"
  if (-not (Test-Path $guardPs1)) {
    throw ("[ERROR] missing file: {0}" -f $guardPs1)
  }

  Run-Step `
    -Title "3) Guard (materialize dated + refresh latest where possible)" `
    -CommandLine "cd `"$ROOT`"; powershell -ExecutionPolicy Bypass -File `"$guardPs1`""
}

Write-Host ""
Write-Host ("[{0}] DONE (run_daily_with_publish)" -f (NowStamp))
exit 0
