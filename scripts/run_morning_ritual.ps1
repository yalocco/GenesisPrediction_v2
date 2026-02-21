# scripts/run_morning_ritual.ps1
# Morning Ritual (single entrypoint)
#
# v2B_invert (threshold=0.02) を主系列として、
# 毎朝：
#   backtest → latest更新 → freeze → daily/monthly report
# まで自動化する完全版

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

# =====================================================
# 1) Core pipeline (既存)
# =====================================================

Run-Step "1) run_daily_with_publish" {
  $p = Join-Path $ROOT "scripts\run_daily_with_publish.ps1"
  if ($Guard) {
    powershell -ExecutionPolicy Bypass -File $p -Date $Date -Guard
  } else {
    powershell -ExecutionPolicy Bypass -File $p -Date $Date
  }
}

Run-Step "2) FX rates" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_rates.ps1")
}

Run-Step "3) FX inputs" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1")
}

Run-Step "4) FX overlay" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1")
}

Run-Step "5) Categories" {
  & $PY (Join-Path $ROOT "scripts\categorize_daily_news.py") --date $Date --latest
}

Run-Step "6) Sentiment build" {
  & $PY (Join-Path $ROOT "scripts\build_daily_sentiment.py") --date $Date
}

Run-Step "7) Normalize sentiment latest" {
  & $PY (Join-Path $ROOT "scripts\normalize_sentiment_latest.py")
}

Run-Step "8) Build sentiment_timeseries.csv" {
  & $PY (Join-Path $ROOT "scripts\build_sentiment_timeseries_csv.py") --date $Date
}

Run-Step "9) Update daily_summary" {
  & $PY (Join-Path $ROOT "scripts\update_daily_summary.py") --date $Date
}

Run-Step "10) Build observation" {
  & $PY (Join-Path $ROOT "scripts\build_daily_observation_log.py") --date $Date
}

Run-Step "11) build_data_health" {
  & $PY (Join-Path $ROOT "scripts\build_data_health.py") --date $Date
}

# =====================================================
# 2) Trend3 v2B_invert Backtest（主系列）
# =====================================================

Run-Step "12) Backtest Trend3 v2B_invert (threshold=0.02)" {
  & $PY (Join-Path $ROOT "scripts\backtest_trend3_fx_v2B_invert.py") --threshold 0.02
}

# 最新JSONを固定名に更新（v2Bのみ採用）
Run-Step "13) Update trend3_fx_latest.json (v2B only)" {

  $BT_DIR = Join-Path $ROOT "analysis\prediction_backtests"

  $latest = Get-ChildItem $BT_DIR -Filter "trend3_fx_v2B_invert_*.json" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

  if (-not $latest) {
    throw "No v2B_invert JSON found."
  }

  $target = Join-Path $BT_DIR "trend3_fx_latest.json"
  Copy-Item $latest.FullName $target -Force

  Write-Host "[OK] Updated trend3_fx_latest.json from v2B"
}

# =====================================================
# 3) Prediction Log Freeze
# =====================================================

Run-Step "14) Save Prediction Log (freeze latest)" {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_save_prediction_log.ps1")
}

# =====================================================
# 4) Daily / Monthly Reports
# =====================================================

Run-Step-NonCritical "15) Build DAILY prediction report" {
  & $PY (Join-Path $ROOT "scripts\report_daily_from_prediction_logs.py")
}

Run-Step-NonCritical "16) Build MONTHLY prediction report" {
  & $PY (Join-Path $ROOT "scripts\report_monthly_from_prediction_logs.py")
}

Write-Host ""
Write-Host ("[{0}] DONE Morning Ritual" -f (NowStamp))
exit 0