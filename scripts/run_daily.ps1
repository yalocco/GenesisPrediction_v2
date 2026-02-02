# scripts/run_daily.ps1
# GenesisPrediction v2 - Daily Runner (stabilized, one-shot)
#
# Includes:
# - docker analyzer
# - build digest view_model
# - publish fx overlay / decision
# - attach fx_block
# - update view_model_latest.json (so GUI default advances)
# - build daily news digest html (latest + dated)
# - ensure daily_news_YYYY-MM-DD.json exists (copy from daily_news_latest.json)
# - build sentiment_latest.json (if possible) + normalize keys for GUI top cards

[CmdletBinding()]
param(
  [string]$Date = "",
  [switch]$NoDocker,
  [switch]$SkipFxOverlay,
  [switch]$SkipFxDecision,
  [switch]$SkipDigestHtml,
  [switch]$SkipSentiment
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
  if (!(Test-Path $py)) { throw "Python not found: $py" }
  return $py
}

# Do NOT use parameter name "$Args" (conflicts with automatic variable)
function Exec([string]$Cmd, [string[]]$CmdArgs) {
  $argText = ""
  if ($null -ne $CmdArgs -and $CmdArgs.Count -gt 0) {
    $argText = " " + ($CmdArgs -join " ")
  }
  Write-Host ">> $Cmd$argText" -ForegroundColor DarkGray
  & $Cmd @CmdArgs
}

function Ensure-Dir([string]$Path) {
  if (!(Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Copy-Force([string]$Src, [string]$Dst) {
  if (!(Test-Path $Src)) {
    Write-Host "WARN: missing source: $Src" -ForegroundColor Yellow
    return $false
  }
  Ensure-Dir (Split-Path -Parent $Dst)
  Copy-Item -Force $Src $Dst
  Write-Host "OK: $Dst" -ForegroundColor Green
  return $true
}

# RepoRoot resolution (this file is under scripts/)
$thisScript = $MyInvocation.MyCommand.Path
$scriptDir  = Split-Path -Parent $thisScript
$RepoRoot   = Split-Path -Parent $scriptDir

Push-Location $RepoRoot
try {
  $d  = Resolve-Date $Date
  $py = Ensure-VenvPython $RepoRoot

  Write-Section "GenesisPrediction v2 | Daily Runner | date=$d"
  Write-Host ("RepoRoot: " + $RepoRoot) -ForegroundColor DarkGray

  $analysisDir = Join-Path $RepoRoot "data\world_politics\analysis"
  $viewDir     = Join-Path $RepoRoot "data\digest\view"
  Ensure-Dir $analysisDir
  Ensure-Dir $viewDir

  # 1) Analyzer (Docker) - optional
  if (-not $NoDocker) {
    Write-Section "1) Analyzer (docker compose run --rm analyzer)"
    Exec "docker" @("compose", "run", "--rm", "analyzer")
  } else {
    Write-Section "1) Analyzer skipped (-NoDocker)"
  }

  # 2) Build Digest ViewModel
  Write-Section "2) Build Digest ViewModel (scripts/build_digest_view_model.py)"
  Exec $py @("scripts/build_digest_view_model.py", "--date", $d)

  # 2.1) Update ViewModel latest pointer so GUI default advances
  Write-Section "2.1) Update ViewModel latest pointer"
  $vmDated  = Join-Path $RepoRoot ("data\digest\view\" + $d + ".json")
  $vmLatest = Join-Path $RepoRoot "data\digest\view_model_latest.json"
  Copy-Force $vmDated $vmLatest | Out-Null

  # 3) Publish FX overlay
  if (-not $SkipFxOverlay) {
    Write-Section "3) Publish FX overlay (scripts/publish_fx_overlay_to_analysis.py)"
    if (Test-Path "scripts/publish_fx_overlay_to_analysis.py") {
      Exec $py @("scripts/publish_fx_overlay_to_analysis.py", "--date", $d)
    } else {
      Write-Host "WARN: scripts/publish_fx_overlay_to_analysis.py not found. Skipping." -ForegroundColor Yellow
    }
  } else {
    Write-Section "3) FX overlay skipped (-SkipFxOverlay)"
  }

  # 4) Publish FX decision
  if (-not $SkipFxDecision) {
    Write-Section "4) Publish FX decision (scripts/publish_fx_decision_to_analysis.py)"
    Exec $py @("scripts/publish_fx_decision_to_analysis.py", "--date", $d)
  } else {
    Write-Section "4) FX decision skipped (-SkipFxDecision)"
  }

  # 5) Attach fx_block to ViewModel
  if (-not $SkipFxDecision) {
    Write-Section "5) Attach fx_block to ViewModel (scripts/attach_fx_block_to_view_model.py)"
    Exec $py @("scripts/attach_fx_block_to_view_model.py", "--date", $d)
  }

  # 6) Build Daily News Digest HTML (latest + dated)
  if (-not $SkipDigestHtml) {
    Write-Section "6) Build Daily News Digest HTML (scripts/build_daily_news_digest.py)"
    if (Test-Path "scripts/build_daily_news_digest.py") {
      Exec $py @("scripts/build_daily_news_digest.py", "--date", $d)
    } else {
      Write-Host "WARN: scripts/build_daily_news_digest.py not found. Skipping digest html." -ForegroundColor Yellow
    }
  } else {
    Write-Section "6) Digest HTML skipped (-SkipDigestHtml)"
  }

  # 7) Ensure daily_news_YYYY-MM-DD.json exists (needed by build_daily_sentiment.py)
  Write-Section "7) Ensure daily_news dated exists"
  $dailyNewsLatest = Join-Path $RepoRoot "data\world_politics\analysis\daily_news_latest.json"
  $dailyNewsDated  = Join-Path $RepoRoot ("data\world_politics\analysis\daily_news_" + $d + ".json")
  $okNews = Copy-Force $dailyNewsLatest $dailyNewsDated

  # 8) Build sentiment_latest.json (and normalize keys for GUI)
  if (-not $SkipSentiment) {
    Write-Section "8) Build Sentiment (scripts/build_daily_sentiment.py) + normalize"
    if ((Test-Path "scripts/build_daily_sentiment.py") -and $okNews) {
      Exec $py @("scripts/build_daily_sentiment.py", "--date", $d)

      if (Test-Path "scripts/normalize_sentiment_latest.py") {
        Exec $py @("scripts/normalize_sentiment_latest.py")
      } else {
        Write-Host "WARN: scripts/normalize_sentiment_latest.py not found. Skipping normalization." -ForegroundColor Yellow
      }
    } else {
      Write-Host "WARN: sentiment skipped (missing build_daily_sentiment.py or daily_news dated)." -ForegroundColor Yellow
    }
  } else {
    Write-Section "8) Sentiment skipped (-SkipSentiment)"
  }

  # 9) Output check
  Write-Section "9) Output check"
  $sentLatest = Join-Path $RepoRoot "data\world_politics\analysis\sentiment_latest.json"
  $digestLatest = Join-Path $RepoRoot "data\world_politics\analysis\daily_news_digest_latest.html"

  foreach ($p in @($vmDated, $vmLatest, $dailyNewsDated, $sentLatest, $digestLatest)) {
    if (Test-Path $p) { Write-Host "OK: $p" -ForegroundColor Green }
    else { Write-Host "MISSING: $p" -ForegroundColor Yellow }
  }

  Write-Section "DONE"
  Write-Host ("Open GUI: http://127.0.0.1:8000/static/index.html") -ForegroundColor Cyan
  Write-Host ("Tip: Ctrl+F5 (hard refresh) if cached") -ForegroundColor Cyan
}
finally {
  Pop-Location
}
