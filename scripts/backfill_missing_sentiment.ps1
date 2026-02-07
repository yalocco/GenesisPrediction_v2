# scripts/backfill_missing_sentiment.ps1
# GenesisPrediction v2
# Backfill missing sentiment_YYYY-MM-DD.json
# - Ensures analysis/daily_news_YYYY-MM-DD.json exists (materialize from raw if missing)
# - Optionally repairs broken raw JSON (Extra data) via scripts/repair_daily_news_json.py
# - Then runs scripts/build_daily_sentiment.py --date YYYY-MM-DD
# - Finally rebuilds sentiment_timeseries.csv via scripts/build_sentiment_timeseries_csv.py
#
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts\backfill_missing_sentiment.ps1 -Days 60
#   powershell -ExecutionPolicy Bypass -File scripts\backfill_missing_sentiment.ps1 -Days 60 -DryRun

param(
  [int]$Days = 30,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section([string]$title) {
  Write-Host ""
  Write-Host ("=" * 60)
  Write-Host $title
  Write-Host ("=" * 60)
}

function Ensure-Dir([string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return }
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function Read-TextUtf8Loose([string]$path) {
  try { return Get-Content -Raw -LiteralPath $path -Encoding UTF8 } catch { }
  try { return Get-Content -Raw -LiteralPath $path } catch { }
  return ""
}

function Write-TextUtf8([string]$path, [string]$text) {
  Ensure-Dir (Split-Path $path)
  if ($DryRun) {
    Write-Host ("[DRY] write: {0} ({1} chars)" -f $path, $text.Length)
    return
  }
  Set-Content -LiteralPath $path -Value $text -Encoding UTF8
  Write-Host ("[OK] wrote: {0}" -f $path)
}

function Try-RepairRawJson([string]$pyExe, [string]$repairScript, [string]$rawPath) {
  if (-not (Test-Path $repairScript)) { return }
  if (-not (Test-Path $rawPath)) { return }

  Write-Host ("[INFO] repair_daily_news_json {0}" -f (Split-Path $rawPath -LeafBase))
  if ($DryRun) {
    Write-Host ("[DRY] python {0} {1}" -f $repairScript, $rawPath)
    return
  }

  & $pyExe $repairScript $rawPath 2>&1 | Out-Host
  # repair tool itself prints OK/WARN; we won't fail the whole run on nonzero here
}

function Materialize-AnalysisDailyNews([string]$rawPath, [string]$dstPath, [string]$dateStr) {
  if (Test-Path $dstPath) {
    Write-Host ("[OK] exists: {0}" -f $dstPath)
    return $true
  }
  if (-not (Test-Path $rawPath)) {
    Write-Host ("[WARN] raw missing: {0}" -f $rawPath)
    return $false
  }

  $raw = Read-TextUtf8Loose $rawPath
  if ([string]::IsNullOrWhiteSpace($raw)) {
    Write-Host ("[WARN] raw empty: {0}" -f $rawPath)
    return $false
  }

  $o = $null
  try {
    $o = $raw | ConvertFrom-Json -Depth 64
  } catch {
    Write-Host ("[WARN] raw JSON parse failed: {0}" -f $rawPath)
    return $false
  }

  $articles = @()
  if ($null -ne $o.articles) {
    foreach ($a in $o.articles) {
      $articles += [pscustomobject]@{
        title       = $a.title
        url         = $a.url
        publishedAt = $a.publishedAt
        description = $a.description
        image       = $a.urlToImage
        source      = $(if ($null -ne $a.source) { $a.source.name } else { $null })
      }
    }
  }

  $out = [pscustomobject]@{
    date         = $dateStr
    fetched_at   = $(if ($null -ne $o.fetched_at) { $o.fetched_at } elseif ($null -ne $o.fetchedAt) { $o.fetchedAt } else { $null })
    query        = $(if ($null -ne $o.query) { $o.query } else { $null })
    totalResults = $(if ($null -ne $o.totalResults) { $o.totalResults } else { $articles.Count })
    articles     = $articles
  }

  Write-TextUtf8 $dstPath (($out | ConvertTo-Json -Depth 64) + "`n")
  Write-Host ("[OK] materialized daily_news ({0})" -f $dateStr)
  return $true
}

# ------------------------------------------------------------
# Context
# ------------------------------------------------------------
$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ROOT

$PY = (Resolve-Path ".\.venv\Scripts\python.exe").Path

$REPAIR     = Join-Path $ROOT "scripts\repair_daily_news_json.py"
$BUILD_SENT = Join-Path $ROOT "scripts\build_daily_sentiment.py"
$BUILD_TS   = Join-Path $ROOT "scripts\build_sentiment_timeseries_csv.py"

$RAW_DIR    = Join-Path $ROOT "data\world_politics"
$AN_DIR     = Join-Path $ROOT "data\world_politics\analysis"
Ensure-Dir $AN_DIR

$to   = Get-Date
$from = $to.AddDays(-$Days)

Write-Section "0) Context"
Write-Host ("[OK] ROOT : {0}" -f $ROOT)
Write-Host ("[OK] PY   : {0}" -f $PY)
Write-Host ("[OK] DryRun: {0}" -f ([bool]$DryRun))
Write-Host ("[OK] Range: {0} .. {1} ({2} days)" -f $from.ToString("yyyy-MM-dd"), $to.ToString("yyyy-MM-dd"), $Days)

# ------------------------------------------------------------
# 1) Detect gaps (raw exists but sentiment missing)
# ------------------------------------------------------------
$targets = @()

for ($d = $from; $d -le $to; $d = $d.AddDays(1)) {
  $ds = $d.ToString("yyyy-MM-dd")
  $raw  = Join-Path $RAW_DIR "$ds.json"
  $sent = Join-Path $AN_DIR "sentiment_$ds.json"
  if ((Test-Path $raw) -and (-not (Test-Path $sent))) {
    $targets += $ds
  }
}

Write-Section "1) Detect gaps (raw exists but sentiment missing)"
if ($targets.Count -eq 0) {
  Write-Host "[OK] targets: 0"
} else {
  Write-Host ("[OK] targets: {0}" -f $targets.Count)
  Write-Host ("[OK] {0}" -f ($targets -join ", "))
}

# ------------------------------------------------------------
# 2) Backfill missing sentiment
# ------------------------------------------------------------
Write-Section "2) Backfill missing sentiment"

$ok = 0
$fail = 0

foreach ($ds in $targets) {
  Write-Host ""
  Write-Host ("[INFO] {0}" -f $ds)

  $rawPath = Join-Path $RAW_DIR "$ds.json"
  $newsAnalysis = Join-Path $AN_DIR "daily_news_$ds.json"

  # (A) Repair raw if tool exists
  Try-RepairRawJson $PY $REPAIR $rawPath

  # (B) Ensure analysis/daily_news exists (materialize from raw)
  $hasNews = Materialize-AnalysisDailyNews $rawPath $newsAnalysis $ds
  if (-not $hasNews) {
    Write-Host ("[WARN] skip sentiment build (daily_news unavailable): {0}" -f $ds)
    $fail += 1
    continue
  }

  # (C) Build sentiment for that date
  if ($DryRun) {
    Write-Host ("[DRY] python {0} --date {1}" -f $BUILD_SENT, $ds)
    $ok += 1
    continue
  }

  & $PY $BUILD_SENT --date $ds 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("[WARN] build_daily_sentiment failed (allowed): {0}" -f $ds)
    $fail += 1
    continue
  }

  Write-Host ("[OK] sentiment built: {0}" -f $ds)
  $ok += 1
}

Write-Host ""
Write-Host ("[OK] success: {0}" -f $ok)
Write-Host ("[NG] failed : {0}" -f $fail)

# ------------------------------------------------------------
# 3) Rebuild sentiment_timeseries.csv
# ------------------------------------------------------------
Write-Section "3) Rebuild sentiment_timeseries.csv"

if ($DryRun) {
  Write-Host ("[DRY] python {0}" -f $BUILD_TS)
} else {
  & $PY $BUILD_TS 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] rebuild timeseries failed (allowed)"
  } else {
    Write-Host "[OK] timeseries rebuilt"
  }
}

Write-Host ""
Write-Host "DONE (backfill_missing_sentiment)"
