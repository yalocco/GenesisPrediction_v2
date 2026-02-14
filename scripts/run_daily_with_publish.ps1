# scripts/run_daily_with_publish.ps1
# One-command daily pipeline (Analyzer -> daily_news publish -> sentiment -> view_model -> publish)
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1 -Date 2026-02-14
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1 -RunGuard
#
# Notes:
# - Date default is UTC "today" to avoid local timezone drift.
# - Stops immediately on error (fail-fast).
# - Calls:
#   1) docker compose run --rm analyzer
#   2) scripts/publish_daily_news_latest.ps1 -Date <date>
#   3) python scripts/build_daily_sentiment.py --date <date>
#   4) python scripts/build_world_view_model_latest.py  (tries --date first, then no-arg fallback)
#   5) scripts/publish_view_model_latest.ps1
#   6) (optional) scripts/run_daily_guard.ps1

[CmdletBinding()]
param(
  [string]$Date,
  [switch]$RunGuard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Step([string]$title, [scriptblock]$body) {
  $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
  Write-Host ""
  Write-Host "[$ts] === $title ===" -ForegroundColor Cyan
  & $body
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
    throw "[ERR] Step failed: $title (exit=$LASTEXITCODE)"
  }
}

function Resolve-Root() {
  # script dir = <root>\scripts
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Ensure-File([string]$path) {
  if (-not (Test-Path $path)) {
    throw "[ERR] missing file: $path"
  }
}

function Run-PwshFile([string]$file, [string[]]$args) {
  Ensure-File $file
  $cmd = @("powershell", "-ExecutionPolicy", "Bypass", "-File", $file) + $args
  Write-Host ("CMD: " + ($cmd -join " "))
  & powershell -ExecutionPolicy Bypass -File $file @args
  if ($LASTEXITCODE -ne 0) { throw "[ERR] failed: $file (exit=$LASTEXITCODE)" }
}

function Run-Py([string]$pyexe, [string]$file, [string[]]$args) {
  Ensure-File $pyexe
  Ensure-File $file
  $cmd = @($pyexe, $file) + $args
  Write-Host ("CMD: " + ($cmd -join " "))
  & $pyexe $file @args
  if ($LASTEXITCODE -ne 0) { throw "[ERR] failed: $file (exit=$LASTEXITCODE)" }
}

# ----------------------------
# Main
# ----------------------------
$root = Resolve-Root

if (-not $Date -or $Date.Trim() -eq "") {
  # default: UTC date to avoid drift
  $Date = [DateTime]::UtcNow.ToString("yyyy-MM-dd")
}

$pyexe = Join-Path $root ".venv\Scripts\python.exe"

$publishDaily = Join-Path $root "scripts\publish_daily_news_latest.ps1"
$buildSent    = Join-Path $root "scripts\build_daily_sentiment.py"
$buildWorldVM = Join-Path $root "scripts\build_world_view_model_latest.py"
$publishVMLat = Join-Path $root "scripts\publish_view_model_latest.ps1"
$guard        = Join-Path $root "scripts\run_daily_guard.ps1"

Write-Host ""
Write-Host "GenesisPrediction v2 - run_daily_with_publish" -ForegroundColor Green
Write-Host ("ROOT : " + $root)
Write-Host ("DATE : " + $Date + " (default=UTC today)")
Write-Host ("GUARD: " + ($(if ($RunGuard) { "ON" } else { "OFF" })))

Step "1) Analyzer (docker compose run --rm analyzer)" {
  Push-Location $root
  try {
    Write-Host "CMD: docker compose run --rm analyzer"
    docker compose run --rm analyzer
    if ($LASTEXITCODE -ne 0) { throw "[ERR] analyzer failed (exit=$LASTEXITCODE)" }
  } finally {
    Pop-Location
  }
}

Step "2) Publish daily_news_latest (for sentiment pipeline)" {
  Run-PwshFile $publishDaily @("-Date", $Date)
}

Step "3) Build daily sentiment (from analysis/daily_news_<date>.json)" {
  Run-Py $pyexe $buildSent @("--date", $Date)
}

Step "4) Build world view_model_latest (for sentiment join)" {
  # Some versions may accept --date, others may not.
  # Try with --date first; if it fails, retry without args.
  try {
    Run-Py $pyexe $buildWorldVM @("--date", $Date)
  } catch {
    Write-Host "[WARN] build_world_view_model_latest.py --date failed; retry without args..." -ForegroundColor Yellow
    Run-Py $pyexe $buildWorldVM @()
  }
}

Step "5) Publish view_model_latest to served /analysis (and dist)" {
  Run-PwshFile $publishVMLat @()
}

if ($RunGuard) {
  Step "6) Guard (optional)" {
    Run-PwshFile $guard @()
  }
}

Write-Host ""
Write-Host "[DONE] run_daily_with_publish completed." -ForegroundColor Green
Write-Host ("Next: open GUI -> http://127.0.0.1:8000/static/index.html?date=" + $Date)
