# scripts/refresh_latest_artifacts.ps1
# Refresh *_latest.json artifacts.
#
# Design:
# - daily_news_latest / daily_summary_latest は "dated -> latest" の SST copy-only
# - sentiment_latest は daily_news と同一世代である必要があるため、ここで再生成して整合させる
#
# Why:
# - 手動で daily_news を更新したのに sentiment を更新しないと、UI join が 0 になる（世代ズレ）
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1 -WhatIf
#
# Options:
#   -RebuildSentiment:$false で sentiment 再生成を止める（非推奨）

[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$AnalysisDir = "data\world_politics\analysis",
  [switch]$RebuildSentiment = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  if ($PSScriptRoot) {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  }
  return (Resolve-Path "..").Path
}

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

function Ensure-Sentiment-InSync {
  param(
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [Parameter(Mandatory=$true)][string]$AnalysisDirAbs,
    [Parameter(Mandatory=$true)][string]$Date
  )

  $py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
  $tool = Join-Path $RepoRoot "scripts\build_daily_sentiment.py"

  if (-not (Test-Path $py)) {
    throw ("[ERROR] python not found: {0}" -f $py)
  }
  if (-not (Test-Path $tool)) {
    throw ("[ERROR] build tool not found: {0}" -f $tool)
  }

  $sentLatest = Join-Path $AnalysisDirAbs "sentiment_latest.json"
  $sentDated  = Join-Path $AnalysisDirAbs ("sentiment_{0}.json" -f $Date)

  # build_daily_sentiment.py reads: daily_news_<date>.json under analysis dir
  # and writes: sentiment_latest.json + sentiment_<date>.json
  $cmd = """$py"" ""$tool"" --date $Date"

  if ($PSCmdlet.ShouldProcess($sentLatest, "Rebuild sentiment for date=$Date (CMD: $cmd)")) {
    Write-Host ("[DO] rebuild sentiment: date={0}" -f $Date)
    & $py $tool --date $Date
    if ($LASTEXITCODE -ne 0) {
      throw ("[ERROR] build_daily_sentiment.py failed (exit={0})" -f $LASTEXITCODE)
    }

    if (-not (Test-Path $sentLatest)) {
      throw ("[ERROR] sentiment_latest.json was not created: {0}" -f $sentLatest)
    }
    if (-not (Test-Path $sentDated)) {
      throw ("[ERROR] sentiment dated file was not created: {0}" -f $sentDated)
    }

    Write-Host ("[OK] sentiment rebuilt and synced to daily_news_{0}.json" -f $Date)
  }
}

# -----------------------------
# Main
# -----------------------------
$ROOT = Resolve-RepoRoot

# Normalize analysis dir to absolute path
$analysisAbs = Join-Path $ROOT $AnalysisDir

Write-Host "=== Refresh latest artifacts (SST copy + sentiment sync) ==="
Write-Host "RepoRoot  : $ROOT"
Write-Host "AnalysisDir: $AnalysisDir"
Write-Host ""

# 1) Copy daily_news_latest + daily_summary_latest from newest dated files
$latestNews = Copy-Latest -Dir $analysisAbs -Prefix "daily_news"
Copy-Latest -Dir $analysisAbs -Prefix "daily_summary" | Out-Null

# 2) Rebuild sentiment so it matches the same date as daily_news_latest
if ($RebuildSentiment) {
  if ($null -eq $latestNews) {
    Write-Warning "daily_news dated file not found; skipping sentiment rebuild."
  } else {
    Ensure-Sentiment-InSync -RepoRoot $ROOT -AnalysisDirAbs $analysisAbs -Date $latestNews.Date
  }
} else {
  Write-Warning "RebuildSentiment is OFF. Sentiment may drift from daily_news."
  # keep legacy behavior: copy latest sentiment dated file if any
  Copy-Latest -Dir $analysisAbs -Prefix "sentiment" | Out-Null
}

Write-Host ""
Write-Host "Done."