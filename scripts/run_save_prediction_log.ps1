# scripts/run_save_prediction_log.ps1
# GenesisPrediction v2 - Research Log Freeze (Prediction Log Saver)
#
# Purpose:
# - "研究ログ永続化" を毎日確実に実行し、資産を途切れさせない
# - Chat/RAGに依存せず、repo内SST（docs/）運用に自己完結させる
#
# Run (recommended):
#   powershell -ExecutionPolicy Bypass -File scripts/run_save_prediction_log.ps1
#
# Optional:
#   powershell -ExecutionPolicy Bypass -File scripts/run_save_prediction_log.ps1 -Date "2026-02-19"
#
# Notes:
# - Python runner: prefers .venv\Scripts\python.exe (repo root)
# - Assumes: scripts/save_prediction_log.py exists (created in the "研究ログ永続化設計" thread)
# - If it doesn't exist, this script will fail fast with a clear error.

param(
  [string]$Date = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log([string]$msg) {
  $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
  Write-Host "[$ts] $msg"
}

function Resolve-RepoRoot([string]$startDir) {
  $dir = Resolve-Path $startDir
  while ($true) {
    if (Test-Path (Join-Path $dir "docker-compose.yml") -PathType Leaf -ErrorAction SilentlyContinue) { return $dir }
    if (Test-Path (Join-Path $dir ".git") -PathType Container -ErrorAction SilentlyContinue) { return $dir }
    $parent = Split-Path $dir -Parent
    if ($parent -eq $dir) { break }
    $dir = $parent
  }
  throw "Could not locate repo root from: $startDir"
}

try {
  $repoRoot = Resolve-RepoRoot $PSScriptRoot
  Set-Location $repoRoot

  if (-not $Date) {
    $Date = Get-Date -Format "yyyy-MM-dd"
  }

  $pyVenv = Join-Path $repoRoot ".venv\Scripts\python.exe"
  $py = if (Test-Path $pyVenv -PathType Leaf) { $pyVenv } else { "python" }

  $scriptPy = Join-Path $repoRoot "scripts\save_prediction_log.py"
  if (-not (Test-Path $scriptPy -PathType Leaf)) {
    throw "Missing script: $scriptPy (expected by run_save_prediction_log.ps1)"
  }

  Write-Log "Research log freeze start"
  Write-Log "RepoRoot: $repoRoot"
  Write-Log "Python:   $py"
  Write-Log "Date:     $Date"
  Write-Log "CMD:      $py scripts/save_prediction_log.py --date $Date"

  & $py $scriptPy --date $Date
  if ($LASTEXITCODE -ne 0) {
    throw "save_prediction_log.py failed (exit=$LASTEXITCODE)"
  }

  Write-Log "Research log freeze OK"
  exit 0
}
catch {
  Write-Log ("[ERROR] " + $_.Exception.Message)
  exit 1
}
