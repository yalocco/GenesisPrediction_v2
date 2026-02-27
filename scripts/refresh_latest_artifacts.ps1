# scripts/refresh_latest_artifacts.ps1
# Refresh *_latest.json by copying the newest dated artifact that exists.
# Read-only / SST: no recalculation (except sentiment sync), only file selection + copy.
#
# - daily_news_latest.json     <- latest daily_news_YYYY-MM-DD.json
# - daily_summary_latest.json  <- latest daily_summary_YYYY-MM-DD.json
# - view_model_latest.json     <- latest view_model_YYYY-MM-DD.json (NEW)
# - sentiment_latest.json      <- rebuilt to match the chosen daily_news date (SYNC)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1 -WhatIf

[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$AnalysisDir = "data\world_politics\analysis"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  try {
    $p = Resolve-Path (Join-Path $PSScriptRoot "..")
    return $p.Path
  } catch {
    return (Get-Location).Path
  }
}

$RepoRoot = Resolve-RepoRoot
$PyExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BuildSent = Join-Path $RepoRoot "scripts\build_daily_sentiment.py"

function Get-LatestDatedFile {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Prefix
  )

  if (-not (Test-Path $Dir)) { return $null }

  $rx = "^" + [Regex]::Escape($Prefix) + "_(?<d>\d{4}-\d{2}-\d{2})\.json$"

  $candidates = Get-ChildItem -Path $Dir -File -Filter "${Prefix}_*.json" |
    ForEach-Object {
      $m = [regex]::Match($_.Name, $rx)
      if ($m.Success) {
        [pscustomobject]@{
          Path = $_.FullName
          Date = $m.Groups["d"].Value
        }
      }
    } |
    Where-Object { $_ -ne $null }

  if (-not $candidates) { return $null }

  return ($candidates | Sort-Object Date | Select-Object -Last 1)
}

function Copy-Latest {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Prefix
  )

  $latest = Get-LatestDatedFile -Dir $Dir -Prefix $Prefix
  if ($null -eq $latest) {
    Write-Warning "No dated files found for prefix '$Prefix' in: $Dir"
    return $null
  }

  $src = $latest.Path
  $dst = Join-Path $Dir "${Prefix}_latest.json"

  if ($PSCmdlet.ShouldProcess($dst, "Copy from $src")) {
    Copy-Item $src $dst -Force
    Write-Host "[OK] $Prefix -> $($latest.Date)"
  }

  return $latest
}

function Rebuild-Sentiment {
  param(
    [Parameter(Mandatory=$true)][string]$Date
  )

  if (-not (Test-Path $PyExe)) {
    throw "python exe not found: $PyExe"
  }
  if (-not (Test-Path $BuildSent)) {
    throw "sentiment builder not found: $BuildSent"
  }

  $cmd = "`"$PyExe`" `"$BuildSent`" --date $Date"
  if ($PSCmdlet.ShouldProcess((Join-Path $AnalysisDir "sentiment_latest.json"), "Rebuild sentiment for date=$Date (CMD: $cmd)")) {
    Write-Host "[DO] rebuild sentiment: date=$Date"
    & $PyExe $BuildSent --date $Date
    if ($LASTEXITCODE -ne 0) { throw "sentiment rebuild failed (exit=$LASTEXITCODE)" }
    Write-Host "[OK] sentiment rebuilt and synced to daily_news_$Date.json"
  }
}

Write-Host "=== Refresh latest artifacts (SST copy + sentiment sync) ==="
Write-Host ("RepoRoot  : " + $RepoRoot)
Write-Host ("AnalysisDir: " + $AnalysisDir)
Write-Host ""

# 1) Copy latest daily_news / daily_summary / view_model
$news   = Copy-Latest -Dir $AnalysisDir -Prefix "daily_news"
$sum    = Copy-Latest -Dir $AnalysisDir -Prefix "daily_summary"
$vm     = Copy-Latest -Dir $AnalysisDir -Prefix "view_model"

Write-Host ""

# 2) Sentiment must match the daily_news date (anti-regression)
if ($null -ne $news -and $news.Date) {
  Rebuild-Sentiment -Date $news.Date
} else {
  Write-Warning "Skip sentiment rebuild: daily_news latest date not found."
}

Write-Host ""
Write-Host "Done."