# scripts/run_morning_ritual.ps1
# Morning Ritual (single entrypoint)
#
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-22
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Guard
#
# Notes:
# - Date is treated as UTC day key (yyyy-MM-dd).
# - Switch params (e.g., -RunGuard) are passed ONLY when enabled (never "OFF" strings).
# - External script invocations use argument arrays (never one big string).

[CmdletBinding()]
param(
  [string]$Date,
  [switch]$Guard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") }

function Write-Section([string]$Title) {
  Write-Host ""
  Write-Host ("[{0}] === {1} ===" -f (NowStamp), $Title)
}

function Resolve-Root {
  try { return (Resolve-Path ".").Path } catch { return (Get-Location).Path }
}

$ROOT = Resolve-Root

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

function Test-File([string]$Path) {
  return (Test-Path $Path)
}

function Require-File([string]$Path, [string]$Label) {
  if (-not (Test-Path $Path)) {
    throw ("Missing required file: {0} => {1}" -f $Label, $Path)
  }
}

function Exec-Python {
  param(
    [Parameter(Mandatory=$true)][string]$ScriptPath,
    [Parameter()][string[]]$Args = @()
  )
  Require-File -Path $ScriptPath -Label $ScriptPath

  $cmdLine = @($PY, $ScriptPath) + $Args
  Write-Host ("CMD: {0}" -f (($cmdLine | ForEach-Object { if ($_ -match '\s') { '"{0}"' -f $_ } else { $_ } }) -join " "))

  & $PY $ScriptPath @Args
  $ec = $LASTEXITCODE
  if ($ec -ne 0) {
    throw ("Python failed (exit={0}): {1}" -f $ec, $ScriptPath)
  }
}

function Exec-Ps1 {
  param(
    [Parameter(Mandatory=$true)][string]$ScriptPath,
    [Parameter()][string[]]$Args = @()
  )
  Require-File -Path $ScriptPath -Label $ScriptPath

  # Use powershell.exe explicitly to avoid call-operator string pitfalls
  $ps = "powershell"
  $cmdLine = @($ps, "-ExecutionPolicy", "Bypass", "-File", $ScriptPath) + $Args
  Write-Host ("CMD: {0}" -f (($cmdLine | ForEach-Object { if ($_ -match '\s') { '"{0}"' -f $_ } else { $_ } }) -join " "))

  & $ps -ExecutionPolicy Bypass -File $ScriptPath @Args
  $ec = $LASTEXITCODE
  if ($ec -ne 0) {
    throw ("PowerShell script failed (exit={0}): {1}" -f $ec, $ScriptPath)
  }
}

function Step {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][ScriptBlock]$Action
  )
  Write-Section $Title
  & $Action
}

function Step-Optional {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][ScriptBlock]$Action
  )
  Write-Section $Title
  try {
    & $Action
  } catch {
    Write-Host ("[WARN] optional step failed: {0}" -f $Title)
    Write-Host ("       {0}" -f $_.Exception.Message)
  }
}

# ----------------------------
# Paths (repo-relative)
# ----------------------------
$PS_RUN_DAILY_WITH_PUBLISH = Join-Path $ROOT "scripts\run_daily_with_publish.ps1"
$PS_FX_RATES              = Join-Path $ROOT "scripts\run_daily_fx_rates.ps1"
$PS_FX_INPUTS             = Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1"
$PS_FX_OVERLAY            = Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1"
$PS_CATEGORIES            = Join-Path $ROOT "scripts\run_daily_categories.ps1"
$PS_SAVE_PRED_LOG         = Join-Path $ROOT "scripts\run_save_prediction_log.ps1"

$PY_BUILD_DAILY_SENTIMENT  = Join-Path $ROOT "scripts\build_daily_sentiment.py"
$PY_NORMALIZE_SENTIMENT    = Join-Path $ROOT "scripts\normalize_sentiment_latest.py"

# sentiment timeseries candidates (natural-heal)
$PY_SENTIMENT_TS_FULL      = Join-Path $ROOT "scripts\rebuild_sentiment_timeseries_full.py"
$PY_SENTIMENT_TS_REBUILD   = Join-Path $ROOT "scripts\rebuild_sentiment_timeseries_csv.py"
$PY_SENTIMENT_TS_BUILD     = Join-Path $ROOT "scripts\build_sentiment_timeseries_csv.py"

$PY_DAILY_SUMMARY_INDEX    = Join-Path $ROOT "scripts\build_daily_summary_index.py"

# observation candidates (natural-heal)
$PY_BUILD_OBSERVATION_LOG  = Join-Path $ROOT "scripts\build_daily_observation_log.py"
$PY_UPDATE_OBSERVATION_MD  = Join-Path $ROOT "scripts\update_observation_md.py"

$PY_BUILD_HEALTH           = Join-Path $ROOT "scripts\build_data_health.py"

$PY_REPORT_DAILY           = Join-Path $ROOT "scripts\report_daily_from_prediction_logs.py"
$PY_REPORT_MONTHLY         = Join-Path $ROOT "scripts\report_monthly_from_prediction_logs.py"

# ----------------------------
# 1) run_daily_with_publish
# ----------------------------
Step "1) run_daily_with_publish" {
  $args = @("-Date", $Date)
  if ($Guard) { $args += "-RunGuard" }   # switch: only when ON
  Exec-Ps1 -ScriptPath $PS_RUN_DAILY_WITH_PUBLISH -Args $args
}

# ----------------------------
# 2) FX rates
# ----------------------------
Step "2) FX rates" {
  Exec-Ps1 -ScriptPath $PS_FX_RATES -Args @()
}

# ----------------------------
# 3) FX inputs
# ----------------------------
Step "3) FX inputs" {
  Exec-Ps1 -ScriptPath $PS_FX_INPUTS -Args @()
}

# ----------------------------
# 4) FX overlay (refresh)
# ----------------------------
Step "4) FX overlay (refresh)" {
  Exec-Ps1 -ScriptPath $PS_FX_OVERLAY -Args @()
}

# ----------------------------
# 5) Categories
# ----------------------------
Step-Optional "5) Categories" {
  if (Test-File $PS_CATEGORIES) {
    Exec-Ps1 -ScriptPath $PS_CATEGORIES -Args @()
  } else {
    Write-Host "[SKIP] scripts/run_daily_categories.ps1 not found"
  }
}

# ----------------------------
# 6) Sentiment build (must pass --date)
# ----------------------------
Step-Optional "6) Sentiment build" {
  if (Test-File $PY_BUILD_DAILY_SENTIMENT) {
    Exec-Python -ScriptPath $PY_BUILD_DAILY_SENTIMENT -Args @("--date", $Date)
  } else {
    Write-Host "[SKIP] scripts/build_daily_sentiment.py not found"
  }
}

# ----------------------------
# 7) Normalize sentiment latest
# ----------------------------
Step-Optional "7) Normalize sentiment latest" {
  if (Test-File $PY_NORMALIZE_SENTIMENT) {
    Exec-Python -ScriptPath $PY_NORMALIZE_SENTIMENT -Args @()
  } else {
    Write-Host "[SKIP] scripts/normalize_sentiment_latest.py not found"
  }
}

# ----------------------------
# 8) Build sentiment_timeseries.csv (natural-heal)
# ----------------------------
Step-Optional "8) Build sentiment_timeseries.csv" {
  if (Test-File $PY_SENTIMENT_TS_FULL) {
    Exec-Python -ScriptPath $PY_SENTIMENT_TS_FULL -Args @()
  } elseif (Test-File $PY_SENTIMENT_TS_REBUILD) {
    Exec-Python -ScriptPath $PY_SENTIMENT_TS_REBUILD -Args @()
  } elseif (Test-File $PY_SENTIMENT_TS_BUILD) {
    Exec-Python -ScriptPath $PY_SENTIMENT_TS_BUILD -Args @()
  } else {
    Write-Host "[SKIP] sentiment_timeseries builder not found (rebuild_* / build_*_csv)"
  }
}

# ----------------------------
# 9) Update daily_summary index
# ----------------------------
Step-Optional "9) Update daily_summary" {
  if (Test-File $PY_DAILY_SUMMARY_INDEX) {
    Exec-Python -ScriptPath $PY_DAILY_SUMMARY_INDEX -Args @("--date", $Date)
  } else {
    Write-Host "[SKIP] scripts/build_daily_summary_index.py not found"
  }
}

# ----------------------------
# 10) Build observation (natural-heal)
# ----------------------------
Step-Optional "10) Build observation" {
  if (Test-File $PY_BUILD_OBSERVATION_LOG) {
    # Most likely expects --date
    Exec-Python -ScriptPath $PY_BUILD_OBSERVATION_LOG -Args @("--date", $Date)
  } elseif (Test-File $PY_UPDATE_OBSERVATION_MD) {
    # Some versions may or may not require --date. Try with --date, then fallback to no-args.
    try {
      Exec-Python -ScriptPath $PY_UPDATE_OBSERVATION_MD -Args @("--date", $Date)
    } catch {
      Write-Host "[WARN] update_observation_md.py failed with --date; retrying without args..."
      Exec-Python -ScriptPath $PY_UPDATE_OBSERVATION_MD -Args @()
    }
  } else {
    Write-Host "[SKIP] observation builder not found (build_daily_observation_log.py / update_observation_md.py)"
  }
}

# ----------------------------
# 11) build_data_health
# ----------------------------
Step-Optional "11) build_data_health" {
  if (Test-File $PY_BUILD_HEALTH) {
    Exec-Python -ScriptPath $PY_BUILD_HEALTH -Args @("--date", $Date)
  } else {
    Write-Host "[SKIP] scripts/build_data_health.py not found"
  }
}

# ----------------------------
# 12) Save Prediction Log (freeze latest)  ※既存ps1に委譲
# ----------------------------
Step-Optional "12) Save Prediction Log (freeze latest)" {
  if (Test-File $PS_SAVE_PRED_LOG) {
    Exec-Ps1 -ScriptPath $PS_SAVE_PRED_LOG -Args @("-Date", $Date)
  } else {
    Write-Host "[SKIP] scripts/run_save_prediction_log.ps1 not found"
  }
}

# ----------------------------
# 13) Build DAILY prediction report
# ----------------------------
Step-Optional "13) Build DAILY prediction report" {
  if (Test-File $PY_REPORT_DAILY) {
    Exec-Python -ScriptPath $PY_REPORT_DAILY -Args @()
  } else {
    Write-Host "[SKIP] scripts/report_daily_from_prediction_logs.py not found"
  }
}

# ----------------------------
# 14) Build MONTHLY prediction report
# ----------------------------
Step-Optional "14) Build MONTHLY prediction report" {
  if (Test-File $PY_REPORT_MONTHLY) {
    Exec-Python -ScriptPath $PY_REPORT_MONTHLY -Args @()
  } else {
    Write-Host "[SKIP] scripts/report_monthly_from_prediction_logs.py not found"
  }
}

Write-Host ""
Write-Host ("[{0}] DONE Morning Ritual" -f (NowStamp))