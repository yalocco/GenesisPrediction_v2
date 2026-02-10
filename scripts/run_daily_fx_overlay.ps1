# scripts/run_daily_fx_overlay.ps1
# FX Overlay daily runner (rates -> dashboard -> overlay -> publish)
#
# Policy:
# - overlay.html / CSS は触らない
# - index/sentiment は触らない
# - run_daily.ps1 / run_daily_guard.ps1 は基本触らない
# - rates が取れない日でも「止めない」（既存CSVで継続）
# - overlay は生成する
# - publish は必ず実行して analysis 側 latest を更新する
#
param(
  [string]$date = (Get-Date -Format "yyyy-MM-dd"),
  [switch]$strict
)

$ErrorActionPreference = "Stop"

$ROOT   = Resolve-Path "$PSScriptRoot\.."
$LOGDIR = Join-Path $ROOT "logs"
$LOG    = Join-Path $LOGDIR ("fx_overlay_{0}.log" -f $date)

function Ensure-Dir([string]$p) { if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null } }
function Log([string]$msg) {
  Ensure-Dir $LOGDIR
  $ts = Get-Date -Format "HH:mm:ss"
  $line = "[{0}] {1}" -f $ts, $msg
  Add-Content -Path $LOG -Value $line
  Write-Host $line
}

function RunPy([string]$scriptRel, [string[]]$args) {
  $scriptPath = Join-Path $ROOT $scriptRel
  if (-not (Test-Path $scriptPath)) { throw "Python script not found: $scriptPath" }

  $argStr = if ($args -and $args.Count -gt 0) { ($args -join " ") } else { "" }
  Log ("PY  {0} {1}" -f $scriptRel, $argStr)

  Push-Location $ROOT
  try {
    & python $scriptPath @args
    $code = $LASTEXITCODE
  } finally {
    Pop-Location
  }

  if ($code -ne 0) { throw "Python failed ($scriptRel) exit=$code" }
}

function GetDashboardMaxDate([string]$dashboardPath) {
  if (-not (Test-Path $dashboardPath)) { return $null }
  $rows = Import-Csv $dashboardPath
  if (-not $rows -or $rows.Count -eq 0) { return $null }
  return ($rows | Select-Object -Last 1).Date
}

Log ("START FX overlay date={0} strict={1}" -f $date, $strict)
Log ("ROOT: {0}" -f $ROOT)

try {
  $dashboard = Join-Path $ROOT "data\fx\jpy_thb_remittance_dashboard.csv"

  # 0) rates（失敗しても止めない）
  if (Test-Path (Join-Path $ROOT "scripts\fx_materialize_rates.py")) {
    try {
      RunPy "scripts\fx_materialize_rates.py" @("--pair","both")
    } catch {
      Log ("WARN rates step failed -> continue (reason: {0})" -f $_)
    }
  } else {
    Log "WARN: scripts\fx_materialize_rates.py not found; skip rates step"
  }

  # 1) dashboard 更新（--date）
  try {
    RunPy "scripts\fx_remittance_today.py" @("--date", $date)
  } catch {
    Log ("WARN dashboard update failed -> continue with existing dashboard (reason: {0})" -f $_)
  }

  $maxDate = GetDashboardMaxDate $dashboard
  $maxDateStr = if ($null -ne $maxDate) { $maxDate } else { "N/A" }
  Log ("dashboard max Date: {0}" -f $maxDateStr)

  if ($strict -and ($null -eq $maxDate -or $maxDate -ne $date)) {
    Log ("SKIP overlay generation (strict mode; max={0} date={1})" -f $maxDateStr, $date)
    exit 0
  }

  # 2) overlay 生成
  RunPy "scripts\fx_remittance_overlay.py" @()

  # 3) publish（--date は必須）
  RunPy "scripts\publish_fx_overlay_to_analysis.py" @("--date", $date)

  Log "DONE FX overlay"
  exit 0
}
catch {
  Log ("ERROR {0}" -f $_)
  exit 1
}
