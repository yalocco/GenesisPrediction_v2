# scripts/run_daily_categories.ps1
# L2: Categorize daily_news into daily_news_categorized_<DATE>.json + latest
#
# Behavior:
# - First tries the given date (default: today).
# - If the dated input does not exist, categorize_daily_news.py will fallback to the newest daily_news_*.json automatically.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_categories.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_categories.ps1 -Date 2026-02-17
#
param(
  [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$py = Join-Path $repoRoot ".venv\Scripts\python.exe"
$script = Join-Path $repoRoot "scripts\categorize_daily_news.py"

if (!(Test-Path $py)) {
  throw "[ERROR] Python venv not found: $py"
}
if (!(Test-Path $script)) {
  throw "[ERROR] Script not found: $script"
}

Write-Host "[INFO] Categorize daily news for date=$Date"
& $py $script --date $Date --latest
if ($LASTEXITCODE -ne 0) {
  throw "[ERROR] categorize_daily_news.py failed with exit code $LASTEXITCODE"
}

Write-Host "[OK] L2 categorization done."
