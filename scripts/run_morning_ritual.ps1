# scripts/run_morning_ritual.ps1
# Morning Ritual (single entrypoint)
#
# What it does:
# 1) run_daily_with_publish
# 2) FX rates
# 3) FX inputs
# 4) FX overlay (refresh)
# 5) Categories
# 6) Sentiment build
# 7) Normalize sentiment latest
# 8) sentiment_timeseries.csv
# 9) daily_summary update
# 10) observation build
# 11) build_data_health
# 12) Save prediction log (freeze latest → dated persistence)
# 13) Build DAILY prediction report
# 14) Build MONTHLY prediction report
#
# This is the ONLY script you run every morning.

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

function Run-Step-NonCritical {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][ScriptBlock]$Action
  )
  Write-Host ""
  Write-Host ("[{0}] === {1} ===" -f (NowStamp), $Title)
  try {
    & $Action
  } catch {
    Write-Host ("[WARN] non-critical step failed: {0}" -f $_.Exception.Message)
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
Write-Host ("GUARD: {0}" -f ($(if ($Guard) { "ON" } else { "OFF" })))

# 1) Core pipeline
Run-Step "1) run_daily_with_publish" {
  $p = Join-Path $ROOT "scripts\run_daily_with_publish.ps1"
  if ($Guard) {
    powershell -ExecutionPolicy Bypass -File $p -Date $Date -Guard
  } else {
    powershell -ExecutionPolicy Bypass -File $p -Date $Date
  }
}

# 2) FX rates
Run-Step "2) FX rates" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_rates.ps1")
}

# 3) FX inputs
Run-Step "3) FX inputs" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1")
}

# 4) FX overlay
Run-Step "4) FX overlay (refresh)" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1")
}

# 5) Categories
Run-Step "5) Categories" {
  & $PY (Join-Path $ROOT "scripts\categorize_daily_news.py") --date $Date --latest
}

# 6) Sentiment build
Run-Step "6) Sentiment build" {
  & $PY (Join-Path $ROOT "scripts\build_daily_sentiment.py") --date $Date
}

# 7) Normalize sentiment
Run-Step "7) Normalize sentiment latest" {
  & $PY (Join-Path $ROOT "scripts\normalize_sentiment_latest.py")
}

# 8) Sentiment timeseries
Run-Step "8) Build sentiment_timeseries.csv" {
  & $PY (Join-Path $ROOT "scripts\build_sentiment_timeseries_csv.py") --date $Date
}

# 9) daily_summary
Run-Step "9) Update daily_summary" {
  & $PY (Join-Path $ROOT "scripts\update_daily_summary.py") --date $Date
}

# 10) observation
Run-Step "10) Build observation" {
  & $PY (Join-Path $ROOT "scripts\build_daily_observation_log.py") --date $Date
}

# 11) Data Health
Run-Step "11) build_data_health" {
  & $PY (Join-Path $ROOT "scripts\build_data_health.py") --date $Date
}

# 12) Prediction Log Persistence（非致命）
Run-Step-NonCritical "12) Save Prediction Log (freeze latest)" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_save_prediction_log.ps1")
}

# 13) DAILY prediction report
Run-Step-NonCritical "13) Build DAILY prediction report" {
  & $PY (Join-Path $ROOT "scripts\report_daily_from_prediction_logs.py")
}

# 14) MONTHLY prediction report
Run-Step-NonCritical "14) Build MONTHLY prediction report" {
  & $PY (Join-Path $ROOT "scripts\report_monthly_from_prediction_logs.py")
}

Write-Host ""
Write-Host ("[{0}] DONE Morning Ritual" -f (NowStamp))
exit 0