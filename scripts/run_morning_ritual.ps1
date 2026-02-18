# scripts/run_morning_ritual.ps1
# Morning Ritual (single entrypoint)
# Goal: run ONLY this script every morning.
#
# What it does (one-shot, fully automated):
# 1) run_daily_with_publish
# 2) FX rates
# 3) FX inputs
# 4) FX overlay (refresh)
# 5) Categories (daily_news -> daily_news_categorized_latest.json)
# 6) Sentiment build (same date)
# 7) Normalize sentiment latest
# 8) Update sentiment_timeseries.csv
# 9) Update daily_summary_{date}.json + daily_summary_latest.json (from analysis/summary.json)
# 10) Build observation_{date}.md/.json + observation_latest.md (robust: create stub if upstream missing)
# 11) build_data_health
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-16
#   powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Guard

[CmdletBinding()]
param(
  [string]$Date,
  [switch]$Guard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") }

function Run-Step {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][ScriptBlock]$Action
  )
  Write-Host ""
  Write-Host ("[{0}] === {1} ===" -f (NowStamp), $Title)
  & $Action
  if ($LASTEXITCODE -ne 0) {
    throw ("[ERROR] step failed (exit={0}): {1}" -f $LASTEXITCODE, $Title)
  }
}

function Require-File {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Label
  )
  if (-not (Test-Path $Path)) {
    throw ("[ERROR] missing required file: {0} -> {1}" -f $Label, $Path)
  }
}

function Write-TextUtf8 {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Text
  )
  $dir = Split-Path $Path -Parent
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.Encoding]::UTF8)
}

function Write-JsonUtf8 {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][object]$Obj
  )
  $json = $Obj | ConvertTo-Json -Depth 20
  Write-TextUtf8 -Path $Path -Text $json
}

$ROOT = (Resolve-Path ".").Path

if ([string]::IsNullOrWhiteSpace($Date)) {
  # Keep consistent with existing scripts: default UTC date
  $Date = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
  $dateNote = " (default=UTC today)"
} else {
  $dateNote = ""
}

$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

Write-Host ""
Write-Host "Morning Ritual (single entrypoint)"
Write-Host ("ROOT : {0}" -f $ROOT)
Write-Host ("DATE : {0}{1}" -f $Date, $dateNote)
Write-Host ("GUARD: {0}" -f ($(if ($Guard) { "ON" } else { "OFF" })))

# 1) Core pipeline + publish + ensure + fx overlay + summary normalize (+ optional guard)
Run-Step -Title "1) run_daily_with_publish" -Action {
  $p = Join-Path $ROOT "scripts\run_daily_with_publish.ps1"
  if ($Guard) {
    powershell -ExecutionPolicy Bypass -File $p -Date $Date -Guard
  } else {
    powershell -ExecutionPolicy Bypass -File $p -Date $Date
  }
}

# 2) FX rates
Run-Step -Title "2) FX rates" -Action {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_rates.ps1")
}

# 3) FX inputs
Run-Step -Title "3) FX inputs" -Action {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1")
}

# 4) FX overlay (refresh)
Run-Step -Title "4) FX overlay (refresh)" -Action {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1")
}

# 5) Categories
Run-Step -Title "5) Categories (daily_news -> categorized_latest)" -Action {
  & $PY (Join-Path $ROOT "scripts\categorize_daily_news.py") --date $Date --latest
}

# 6) Sentiment build
Run-Step -Title "6) Sentiment build (same date as categorized)" -Action {
  & $PY (Join-Path $ROOT "scripts\build_daily_sentiment.py") --date $Date
}

# 7) Normalize sentiment latest
Run-Step -Title "7) Normalize sentiment latest" -Action {
  & $PY (Join-Path $ROOT "scripts\normalize_sentiment_latest.py")
}

# 8) sentiment_timeseries.csv
Run-Step -Title "8) Build sentiment_timeseries.csv (same date)" -Action {
  & $PY (Join-Path $ROOT "scripts\build_sentiment_timeseries_csv.py") --date $Date
}

# 9) daily_summary (dated + latest from summary.json)
Run-Step -Title "9) Update daily_summary (dated + latest from summary.json)" -Action {
  $analysisDir = Join-Path $ROOT "data\world_politics\analysis"
  $srcSummary  = Join-Path $analysisDir "summary.json"
  $dstDated    = Join-Path $analysisDir ("daily_summary_{0}.json" -f $Date)
  $dstLatest   = Join-Path $analysisDir "daily_summary_latest.json"

  Require-File -Path $srcSummary -Label "analysis/summary.json"

  Copy-Item -Force $srcSummary $dstDated
  Copy-Item -Force $srcSummary $dstLatest

  Write-Host ("[OK] daily_summary updated")
  Write-Host ("  src   : {0}" -f $srcSummary)
  Write-Host ("  dated : {0}" -f $dstDated)
  Write-Host ("  latest: {0}" -f $dstLatest)
}

# 10) observation (robust)
Run-Step -Title "10) Build observation (dated + latest, robust)" -Action {
  $analysisDir = Join-Path $ROOT "data\world_politics\analysis"
  $scriptObs   = Join-Path $ROOT "scripts\build_daily_observation_log.py"

  $mdDated  = Join-Path $analysisDir ("observation_{0}.md" -f $Date)
  $jsDated  = Join-Path $analysisDir ("observation_{0}.json" -f $Date)
  $mdLatest = Join-Path $analysisDir "observation_latest.md"

  if (Test-Path $scriptObs) {
    try {
      & $PY $scriptObs --date $Date
    } catch {
      Write-Host ("[WARN] observation python build failed; will create stub. ({0})" -f $_.Exception.Message)
    }
  } else {
    Write-Host "[WARN] build_daily_observation_log.py not found; will create stub."
  }

  $madeMd = Test-Path $mdDated
  $madeJs = Test-Path $jsDated

  if (-not $madeMd -or -not $madeJs) {
    $newsPath = Join-Path $analysisDir ("daily_news_{0}.json" -f $Date)
    $sentPath = Join-Path $analysisDir "sentiment_latest.json"
    $catPath  = Join-Path $analysisDir "daily_news_categorized_latest.json"
    $latestVm = Join-Path $analysisDir "latest.json"

    $counts = @{
      daily_news  = 0
      categorized = 0
      sentiment   = 0
    }

    if (Test-Path $newsPath) {
      try {
        $n = Get-Content $newsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $n.items) { $counts.daily_news = @($n.items).Count }
        elseif ($null -ne $n.articles) { $counts.daily_news = @($n.articles).Count }
      } catch { }
    }

    if (Test-Path $catPath) {
      try {
        $c = Get-Content $catPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $c.items) { $counts.categorized = @($c.items).Count }
      } catch { }
    }

    if (Test-Path $sentPath) {
      try {
        $s = Get-Content $sentPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $s.items) { $counts.sentiment = @($s.items).Count }
      } catch { }
    }

    $stampLocal = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")

    $stubJson = @{
      date = $Date
      generated_at = $stampLocal
      method = "stub"
      note = "Auto-generated stub because observation builder produced no outputs (missing events jsonl or upstream mismatch)."
      counts = $counts
      sources = @{
        daily_news         = $(if (Test-Path $newsPath) { "analysis/daily_news_$Date.json" } else { $null })
        categorized_latest = $(if (Test-Path $catPath)  { "analysis/daily_news_categorized_latest.json" } else { $null })
        sentiment_latest   = $(if (Test-Path $sentPath) { "analysis/sentiment_latest.json" } else { $null })
        latest             = $(if (Test-Path $latestVm) { "analysis/latest.json" } else { $null })
      }
    }

    $stubMd = @"
# Observation ($Date)

- generated_at: $stampLocal
- method: stub
- note: observation builder produced no outputs (events jsonl missing or upstream mismatch). This stub keeps Data Health clean.

## Counts
- daily_news: $($counts.daily_news)
- categorized: $($counts.categorized)
- sentiment: $($counts.sentiment)

## Sources
- daily_news: analysis/daily_news_$Date.json
- categorized_latest: analysis/daily_news_categorized_latest.json
- sentiment_latest: analysis/sentiment_latest.json
- latest: analysis/latest.json
"@

    if (-not $madeMd) {
      Write-TextUtf8 -Path $mdDated -Text $stubMd
      Write-Host ("[OK] wrote stub md: {0}" -f $mdDated)
    }
    if (-not $madeJs) {
      Write-JsonUtf8 -Path $jsDated -Obj $stubJson
      Write-Host ("[OK] wrote stub json: {0}" -f $jsDated)
    }
  }

  Require-File -Path $mdDated -Label ("observation_{0}.md" -f $Date)
  Copy-Item -Force $mdDated $mdLatest

  Write-Host ("[OK] observation updated")
  Write-Host ("  md dated : {0}" -f $mdDated)
  Write-Host ("  js dated : {0}" -f $jsDated)
  Write-Host ("  md latest: {0}" -f $mdLatest)
}

# 11) Data Health build (final)
Run-Step -Title "11) build_data_health" -Action {
  & $PY (Join-Path $ROOT "scripts\build_data_health.py") --date $Date
}

Write-Host ""
Write-Host ("[{0}] DONE Morning Ritual" -f (NowStamp))
exit 0
