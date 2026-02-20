# scripts/run_save_prediction_log.ps1
# Trend3 FX 研究ログ永続化（固定 latest 更新 → 日次凍結ログ保存）
#
# 目的:
# - analysis/prediction_backtests 配下の「最新 backtest JSON」を見つける
# - 固定名 analysis/prediction_backtests/trend3_fx_latest.json を安全に更新（コピー更新）
# - 日次凍結ログ prediction_log_YYYY-MM-DD.json を保存
#   （可能なら scripts/save_prediction_log.py を呼ぶ。無ければ JSON をそのまま凍結コピー）
#
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts/run_save_prediction_log.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_save_prediction_log.ps1 -Date 2026-02-19
#
# Notes:
# - Windows運用では symlink より「コピー更新」が事故りにくい
# - “最新候補が無い / JSONが壊れている” 場合は latest を更新しない（既存保持）

[CmdletBinding()]
param(
  [string]$Date = "",
  [string]$RepoRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log([string]$level, [string]$msg) {
  $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
  Write-Host "[$ts] [$level] $msg"
}

function Resolve-RepoRoot([string]$maybeRoot) {
  if ($maybeRoot -and (Test-Path $maybeRoot)) {
    return (Resolve-Path $maybeRoot).Path
  }
  # scripts/ の1つ上が repo root
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-UtcDateString([string]$d) {
  if ($d -and $d.Trim().Length -gt 0) {
    return $d.Trim()
  }
  return (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
}

function Test-JsonReadable([string]$path) {
  try {
    $null = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    return $true
  } catch {
    return $false
  }
}

function Copy-Atomic([string]$src, [string]$dst) {
  $dstDir = Split-Path -Parent $dst
  if (!(Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir | Out-Null }

  $tmp = Join-Path $dstDir (".tmp_" + [Guid]::NewGuid().ToString("N") + "_" + (Split-Path -Leaf $dst))
  Copy-Item -LiteralPath $src -Destination $tmp -Force
  Move-Item -LiteralPath $tmp -Destination $dst -Force
}

function Find-LatestCandidate([string]$dir) {
  # 優先順位（強い成果→弱い成果の順）
  $patterns = @(
    "trend3_fx_v2B_invert_*.json",
    "trend3_fx_v2C_walkforward_*.json",
    "trend3_fx_v2A_*.json",
    "trend3_fx_v2_*.json",
    "trend3_fx_v1_*.json",
    "trend3_fx_*.json"
  )

  foreach ($pat in $patterns) {
    $items = Get-ChildItem -LiteralPath $dir -Filter $pat -File -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTimeUtc -Descending
    foreach ($it in $items) {
      if (Test-JsonReadable $it.FullName) {
        return $it.FullName
      }
    }
  }
  return $null
}

# -----------------------------
# main
# -----------------------------
$root = Resolve-RepoRoot $RepoRoot
$utcDate = Get-UtcDateString $Date

$analysisDir = Join-Path $root "analysis"
$backtestsDir = Join-Path $analysisDir "prediction_backtests"
$latestPath = Join-Path $backtestsDir "trend3_fx_latest.json"

$logsDir = Join-Path $analysisDir "prediction_logs"
$datedLog = Join-Path $logsDir ("prediction_log_{0}.json" -f $utcDate)

$pythonExe = Join-Path $root ".venv\Scripts\python.exe"
$savePy = Join-Path $root "scripts\save_prediction_log.py"

Write-Log "INFO" "Run save prediction log"
Write-Log "INFO" ("ROOT={0}" -f $root)
Write-Log "INFO" ("DATE(UTC)={0}" -f $utcDate)
Write-Log "INFO" ("BACKTEST_DIR={0}" -f $backtestsDir)

if (!(Test-Path $backtestsDir)) {
  throw "Backtests dir not found: $backtestsDir"
}

$candidate = Find-LatestCandidate $backtestsDir
if (-not $candidate) {
  Write-Log "WARN" "No readable candidate JSON found. latest will NOT be updated."
  if (Test-Path $latestPath) {
    Write-Log "INFO" "Existing latest remains: $latestPath"
  }
  return
}

Write-Log "INFO" ("Latest candidate: {0}" -f $candidate)

# latest 更新（安全コピー）
try {
  Copy-Atomic $candidate $latestPath
  Write-Log "OK" ("Updated latest: {0}" -f $latestPath)
} catch {
  Write-Log "WARN" ("Failed to update latest (kept existing). err={0}" -f $_.Exception.Message)
  return
}

# 日次凍結ログ
if (!(Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }

# 可能なら Python で永続化（スキーマ付与・追記CSV等を将来ここに集約）
if ((Test-Path $pythonExe) -and (Test-Path $savePy)) {
  Write-Log "INFO" "save_prediction_log.py found. Using python writer."
  $cmd = @(
    $pythonExe,
    $savePy,
    "--date", $utcDate,
    "--prediction-json", $latestPath,
    "--out", $datedLog
  )
  Write-Log "INFO" ("CMD: {0}" -f ($cmd -join " "))
  & $pythonExe $savePy --date $utcDate --prediction-json $latestPath --out $datedLog
  if ($LASTEXITCODE -ne 0) {
    throw "save_prediction_log.py failed with exit code $LASTEXITCODE"
  }
  Write-Log "OK" ("Wrote dated log: {0}" -f $datedLog)
}
else {
  # Pythonが無い/未実装なら「latest JSON をそのまま凍結コピー」
  Write-Log "WARN" "save_prediction_log.py not available. Fallback: freeze-copy latest JSON."
  try {
    Copy-Atomic $latestPath $datedLog
    Write-Log "OK" ("Freeze-copied dated log: {0}" -f $datedLog)
  } catch {
    throw "Failed to write dated log: $datedLog  err=$($_.Exception.Message)"
  }
}

Write-Log "OK" "DONE"
