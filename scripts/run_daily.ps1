# ============================================================
# GenesisPrediction v2 - run_daily.ps1 (A仕様・安定版)
# Home(index)は導線のみ / 正解は Sentiment & Overlay
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function OK($msg)   { Write-Host "[OK]  $msg" -ForegroundColor Green }
function INFO($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function WARN($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function FAIL($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

# ------------------------------------------------------------
# 0) Context
# ------------------------------------------------------------
$ROOT = Resolve-Path "$PSScriptRoot\.."
$DATE = (Get-Date).ToString("yyyy-MM-dd")
$PY   = "$ROOT\.venv\Scripts\python.exe"

Write-Host "============================================================"
Write-Host "0) Context (date=$DATE)"
Write-Host "============================================================"

OK "ROOT: $ROOT"
OK "DATE: $DATE"
OK "PY  : $PY"

if (-not (Test-Path $PY)) {
    FAIL "python not found: $PY"
}

Set-Location $ROOT

# ------------------------------------------------------------
# 1) Fetcher
# ------------------------------------------------------------
Write-Host "`n=== 1) Fetcher ==="
docker compose run --rm fetcher | Out-Host
OK "1) Fetcher"

# ------------------------------------------------------------
# 2) Analyzer
# ------------------------------------------------------------
Write-Host "`n=== 2) Analyzer ==="
docker compose run --rm analyzer | Out-Host
OK "2) Analyzer"

# ------------------------------------------------------------
# 3) Build Digest ViewModel (dated)
# ------------------------------------------------------------
Write-Host "`n=== 3) Build Digest ViewModel ==="
& $PY scripts\build_digest_viewmodel.py --date $DATE
OK "3) Build Digest ViewModel"

# ------------------------------------------------------------
# 4) Normalize sentiment
# ------------------------------------------------------------
Write-Host "`n=== 4) Normalize sentiment ==="
& $PY scripts\normalize_sentiment_latest.py
OK "4) Normalize sentiment"

# ------------------------------------------------------------
# 5) Patch ViewModel sentiment summary (A仕様)
# ------------------------------------------------------------
Write-Host "`n=== 5) Patch sentiment summary (A spec) ==="
& $PY scripts\ensure_view_model_sentiment_summary.py --date $DATE
OK "5) Patch sentiment summary"

# ------------------------------------------------------------
# 6) Build sentiment time-series
# ------------------------------------------------------------
Write-Host "`n=== 6) Build sentiment timeseries ==="
& $PY scripts\build_sentiment_timeseries_csv.py --date $DATE
OK "6) Build sentiment timeseries"

# ------------------------------------------------------------
# 7) Final sanity check (terminal truth)
# ------------------------------------------------------------
Write-Host "`n=== 7) Sanity check ==="

$SENT = "data/world_politics/analysis/sentiment_latest.json"
$VM   = "data/world_politics/analysis/view_model_latest.json"

if (-not (Test-Path $SENT)) { FAIL "missing sentiment_latest.json" }
if (-not (Test-Path $VM))   { FAIL "missing view_model_latest.json" }

$sentObj = Get-Content $SENT | ConvertFrom-Json
$vmObj   = Get-Content $VM   | ConvertFrom-Json

Write-Host ""
Write-Host "---- SENTIMENT (truth) ----"
Write-Host "articles    = $($sentObj.today.articles)"
Write-Host "risk         = $($sentObj.today.risk)"
Write-Host "positive     = $($sentObj.today.positive)"
Write-Host "uncertainty  = $($sentObj.today.uncertainty)"

Write-Host ""
Write-Host "---- VIEW MODEL ----"
Write-Host "articles    = $($vmObj.summary.articles)"
Write-Host "risk         = $($vmObj.summary.risk)"
Write-Host "positive     = $($vmObj.summary.positive)"
Write-Host "uncertainty  = $($vmObj.summary.uncertainty)"

OK "Sanity check passed"

# ------------------------------------------------------------
# 8) Open GUI
# ------------------------------------------------------------
Write-Host "`n=== 8) Open GUI ==="
$URL = "http://127.0.0.1:8000/static/index.html?date=$DATE"
OK "Open GUI: $URL"
Start-Process $URL

Write-Host "`nDONE"
