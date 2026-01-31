# scripts/run_daily.ps1
# GenesisPrediction v2 - Daily Runner (Commercial-grade, read-only GUI / SST)
#
# IMPORTANT:
# - This script may be located under scripts/.
# - RepoRoot is resolved as the parent directory of this script's folder.
#
# Usage (recommended):
#   .\scripts\run_daily.ps1
#   .\scripts\run_daily.ps1 -Date 2026-01-31
#   .\scripts\run_daily.ps1 -NoDocker
#   .\scripts\run_daily.ps1 -SkipFxOverlay
#   .\scripts\run_daily.ps1 -SkipFxDecision
#
[CmdletBinding()]
param(
  [string]$Date = "",
  [switch]$NoDocker,
  [switch]$SkipFxOverlay,
  [switch]$SkipFxDecision
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Section([string]$Title) {
  Write-Host ""
  Write-Host "============================================================" -ForegroundColor Cyan
  Write-Host $Title -ForegroundColor Cyan
  Write-Host "============================================================" -ForegroundColor Cyan
}

function Resolve-Date([string]$DateArg) {
  if ([string]::IsNullOrWhiteSpace($DateArg)) {
    return (Get-Date).ToString("yyyy-MM-dd")
  }
  if ($DateArg -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw "Invalid -Date format. Use YYYY-MM-DD. Given: $DateArg"
  }
  return $DateArg
}

function Ensure-VenvPython([string]$RepoRoot) {
  $py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
  if (!(Test-Path $py)) {
    throw "Python not found: $py  (Did you create venv? .\.venv\Scripts\python.exe)"
  }
  return $py
}

function Exec([string]$Cmd, [string[]]$Args) {
  Write-Host ">> $Cmd $($Args -join ' ')" -ForegroundColor DarkGray
  & $Cmd @Args
}

# ------------------------------------------------------------
# Resolve RepoRoot robustly (this file lives under scripts/)
# ------------------------------------------------------------
$thisScript = $MyInvocation.MyCommand.Path
$scriptDir  = Split-Path -Parent $thisScript
$RepoRoot   = Split-Path -Parent $scriptDir  # parent of scripts/

Push-Location $RepoRoot

try {
  $d  = Resolve-Date $Date
  $py = Ensure-VenvPython $RepoRoot

  Write-Section "GenesisPrediction v2 | Daily Runner | date=$d"
  Write-Host ("RepoRoot: " + $RepoRoot) -ForegroundColor DarkGray

  # ----------------------------------------------------------
  # 0) Preflight
  # ----------------------------------------------------------
  $analysisDir = Join-Path $RepoRoot "data\world_politics\analysis"
  $viewDir     = Join-Path $RepoRoot "data\digest\view"
  if (!(Test-Path $analysisDir)) { New-Item -ItemType Directory -Force -Path $analysisDir | Out-Null }
  if (!(Test-Path $viewDir))     { New-Item -ItemType Directory -Force -Path $viewDir     | Out-Null }

  # ----------------------------------------------------------
  # 1) Analyzer (Docker) - optional
  # ----------------------------------------------------------
  if (-not $NoDocker) {
    Write-Section "1) Analyzer (docker compose run --rm analyzer)"
    Exec "docker" @("compose", "run", "--rm", "analyzer")
  }
  else {
    Write-Section "1) Analyzer skipped (-NoDocker)"
    Write-Host "Skipping docker analyzer step." -ForegroundColor Yellow
  }

  # ----------------------------------------------------------
  # 2) Build Digest ViewModel
  # ----------------------------------------------------------
  Write-Section "2) Build Digest ViewModel (scripts/build_digest_view_model.py)"
  $buildVm = Join-Path $RepoRoot "scripts\build_digest_view_model.py"
  if (!(Test-Path $buildVm)) { throw "Missing script: $buildVm" }
  Exec $py @("scripts/build_digest_view_model.py", "--date", $d)

  # ----------------------------------------------------------
  # 3) Publish FX overlay PNG into analysis (optional)
  # ----------------------------------------------------------
  if (-not $SkipFxOverlay) {
    Write-Section "3) Publish FX overlay into analysis (scripts/publish_fx_overlay_to_analysis.py)"
    $pubFxOverlay = Join-Path $RepoRoot "scripts\publish_fx_overlay_to_analysis.py"
    if (Test-Path $pubFxOverlay) {
      Exec $py @("scripts/publish_fx_overlay_to_analysis.py", "--date", $d)
    }
    else {
      Write-Host "WARN: publish_fx_overlay_to_analysis.py not found. Skipping FX overlay publish." -ForegroundColor Yellow
    }
  }
  else {
    Write-Section "3) FX overlay publish skipped (-SkipFxOverlay)"
  }

  # ----------------------------------------------------------
  # 4) Publish FX decision JSON into analysis (B) (optional)
  # ----------------------------------------------------------
  if (-not $SkipFxDecision) {
    Write-Section "4) Publish FX decision into analysis (scripts/publish_fx_decision_to_analysis.py)"
    $pubFxDecision = Join-Path $RepoRoot "scripts\publish_fx_decision_to_analysis.py"
    if (!(Test-Path $pubFxDecision)) { throw "Missing script: $pubFxDecision" }
    Exec $py @("scripts/publish_fx_decision_to_analysis.py", "--date", $d)
  }
  else {
    Write-Section "4) FX decision publish skipped (-SkipFxDecision)"
  }

  # ----------------------------------------------------------
  # 5) Attach fx_block to ViewModel (C)
  # ----------------------------------------------------------
  if (-not $SkipFxDecision) {
    Write-Section "5) Attach fx_block to ViewModel (C) (scripts/attach_fx_block_to_view_model.py)"
    $attachFx = Join-Path $RepoRoot "scripts\attach_fx_block_to_view_model.py"
    if (!(Test-Path $attachFx)) { throw "Missing script: $attachFx" }
    Exec $py @("scripts/attach_fx_block_to_view_model.py", "--date", $d)
  }
  else {
    Write-Section "5) fx_block attach skipped (because -SkipFxDecision)"
  }

  # ----------------------------------------------------------
  # 6) Output check
  # ----------------------------------------------------------
  Write-Section "6) Output check (paths)"
  $vmOut = Join-Path $RepoRoot ("data\digest\view\" + $d + ".json")
  $fxDec = Join-Path $RepoRoot ("data\world_politics\analysis\fx_decision_" + $d + ".json")
  $fxDecLatest = Join-Path $RepoRoot "data\world_politics\analysis\fx_decision_latest.json"

  Write-Host ("ViewModel: " + $vmOut) -ForegroundColor Green
  if (Test-Path $vmOut) { Write-Host "  OK" -ForegroundColor Green } else { Write-Host "  MISSING" -ForegroundColor Yellow }

  if (-not $SkipFxDecision) {
    Write-Host ("FX decision dated: " + $fxDec) -ForegroundColor Green
    if (Test-Path $fxDec) { Write-Host "  OK" -ForegroundColor Green } else { Write-Host "  MISSING" -ForegroundColor Yellow }

    Write-Host ("FX decision latest: " + $fxDecLatest) -ForegroundColor Green
    if (Test-Path $fxDecLatest) { Write-Host "  OK" -ForegroundColor Green } else { Write-Host "  MISSING" -ForegroundColor Yellow }
  }

  Write-Section "DONE"
  Write-Host "Open GUI (copy into browser):" -ForegroundColor Cyan
  Write-Host ("  http://127.0.0.1:8000/static/index.html?date=" + $d) -ForegroundColor Cyan
  Write-Host "FX card should show:" -ForegroundColor Cyan
  Write-Host ("  Source: view_model:" + $d) -ForegroundColor Cyan
}
finally {
  Pop-Location
}
