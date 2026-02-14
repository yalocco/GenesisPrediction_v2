# scripts/publish_daily_news_latest.ps1
# Publish daily world_politics JSON into analysis/ for sentiment pipeline.
#
# Copies:
#   data/world_politics/YYYY-MM-DD.json
#     -> data/world_politics/analysis/daily_news_YYYY-MM-DD.json
#     -> data/world_politics/analysis/daily_news_latest.json
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/publish_daily_news_latest.ps1 -Date 2026-02-14

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$Date
)

$ErrorActionPreference = "Stop"

function Copy-WithReport([string]$src, [string]$dst) {
  if(!(Test-Path $src)) { throw "SRC not found: $src" }
  $dstDir = Split-Path -Parent $dst
  if(!(Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }

  Copy-Item -Force $src $dst

  $si = Get-Item $src
  $di = Get-Item $dst
  Write-Host "[OK] copied"
  Write-Host ("     SRC: {0}  ({1} bytes, {2})" -f $si.FullName, $si.Length, $si.LastWriteTime)
  Write-Host ("     DST: {0}  ({1} bytes, {2})" -f $di.FullName, $di.Length, $di.LastWriteTime)
}

try {
  $root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

  $src = Join-Path $root ("data\world_politics\{0}.json" -f $Date)
  $dst1 = Join-Path $root ("data\world_politics\analysis\daily_news_{0}.json" -f $Date)
  $dst2 = Join-Path $root "data\world_politics\analysis\daily_news_latest.json"

  Write-Host ""
  Write-Host "[INFO] Publishing daily_news for sentiment pipeline..."
  Write-Host ("       DATE: {0}" -f $Date)
  Write-Host ("       SRC : {0}" -f $src)
  Write-Host ""

  Copy-WithReport $src $dst1
  Copy-WithReport $src $dst2

  Write-Host ""
  Write-Host "[DONE] publish_daily_news_latest completed."
  exit 0
}
catch {
  Write-Host ""
  Write-Host "[ERR] $($_.Exception.Message)"
  exit 1
}
