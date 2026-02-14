# scripts/run_daily_with_publish.ps1
# Wrapper: run daily pipeline + publish artifacts needed by GUI/Sentiment.
# - runs scripts/run_daily.ps1
# - publishes daily_news_latest.json into analysis/
# - rebuilds sentiment_latest.json from that daily_news (stable URL join)
# - publishes view_model_latest.json (served /analysis consistency)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1
#
# Optional:
#   -Date YYYY-MM-DD  (default: today in local time)
#
# Exit codes:
#   0 OK
#   1 run_daily failed
#   2 publish_daily_news_latest failed
#   3 build_daily_sentiment failed
#   4 publish_view_model_latest failed

[CmdletBinding()]
param(
  [string]$Date = $(Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

function Run-Step([string]$Title, [scriptblock]$Block) {
  Write-Host ""
  Write-Host "=== $Title ==="
  & $Block
  Write-Host "[OK] $Title"
}

try {
  $root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

  $runDaily   = Join-Path $root "scripts\run_daily.ps1"
  $pubNews    = Join-Path $root "scripts\publish_daily_news_latest.ps1"
  $buildSent  = Join-Path $root "scripts\build_daily_sentiment.py"
  $pubVM      = Join-Path $root "scripts\publish_view_model_latest.ps1"

  if(!(Test-Path $runDaily))  { throw "Missing: $runDaily" }
  if(!(Test-Path $pubNews))   { throw "Missing: $pubNews" }
  if(!(Test-Path $buildSent)) { throw "Missing: $buildSent" }
  if(!(Test-Path $pubVM))     { throw "Missing: $pubVM" }

  # Use venv python if available
  $py = Join-Path $root ".venv\Scripts\python.exe"
  if(!(Test-Path $py)) { $py = "python" }

  Run-Step "1) run_daily.ps1" {
    powershell -ExecutionPolicy Bypass -File $runDaily
    if($LASTEXITCODE -ne 0){ exit 1 }
  }

  Run-Step "2) publish_daily_news_latest.ps1 ($Date)" {
    powershell -ExecutionPolicy Bypass -File $pubNews -Date $Date
    if($LASTEXITCODE -ne 0){ exit 2 }
  }

  Run-Step "3) build_daily_sentiment.py ($Date)" {
    & $py $buildSent --date $Date
    if($LASTEXITCODE -ne 0){ exit 3 }
  }

  Run-Step "4) publish_view_model_latest.ps1" {
    powershell -ExecutionPolicy Bypass -File $pubVM
    if($LASTEXITCODE -ne 0){ exit 4 }
  }

  Write-Host ""
  Write-Host "[DONE] run_daily_with_publish completed."
  exit 0
}
catch {
  Write-Host ""
  Write-Host "[ERR] $($_.Exception.Message)"
  exit 99
}
