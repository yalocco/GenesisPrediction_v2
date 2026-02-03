param(
  [string]$Date = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function HR($title) {
  Write-Host ""
  Write-Host ("=" * 78) -ForegroundColor DarkCyan
  Write-Host $title -ForegroundColor Cyan
  Write-Host ("=" * 78) -ForegroundColor DarkCyan
}
function OK($msg)   { Write-Host "[OK]  $msg" -ForegroundColor Green }
function WARN($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function ERR($msg)  { Write-Host "[ERR] $msg" -ForegroundColor Red }

# ----------------------------
# Context
# ----------------------------
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $RepoRoot

try {
  $PY = (Resolve-Path ".\.venv\Scripts\python.exe").Path

  if ([string]::IsNullOrWhiteSpace($Date)) {
    # Tokyo local date
    $Date = (Get-Date).ToString("yyyy-MM-dd")
  }

  HR "GenesisPrediction v2 | Daily Runner | date=$Date"
  OK "RepoRoot: $RepoRoot"

  # ----------------------------
  # 1) Analyzer
  # ----------------------------
  HR "1) Analyzer (docker compose run --rm analyzer)"
  & docker compose run --rm analyzer

  # ----------------------------
  # 2) Build Digest ViewModel
  # ----------------------------
  HR "2) Build Digest ViewModel (scripts/build_digest_view_model.py)"
  if (Test-Path "scripts/build_digest_view_model.py") {
    & $PY "scripts/build_digest_view_model.py" --date $Date
  } else {
    WARN "missing script: scripts/build_digest_view_model.py"
  }

  # ----------------------------
  # 2.1) Update ViewModel latest pointer (robust)
  # ----------------------------
  HR "2.1) Update ViewModel latest pointer"
  $VM_DATED   = Join-Path $RepoRoot "data\digest\view\$Date.json"
  $VM_LATEST_A = Join-Path $RepoRoot "data\digest\view_model_latest.json"
  $VM_LATEST_B = Join-Path $RepoRoot "data\digest\view\view_model_latest.json"

  if (Test-Path $VM_DATED) {
    Copy-Item -Force $VM_DATED $VM_LATEST_A
    Copy-Item -Force $VM_DATED $VM_LATEST_B
    OK "updated: $VM_LATEST_A"
    OK "updated: $VM_LATEST_B"
  } else {
    WARN "view_model not found: $VM_DATED"
  }

  # ----------------------------
  # 3) Publish FX overlay
  # ----------------------------
  HR "3) Publish FX overlay (scripts/publish_fx_overlay_to_analysis.py)"
  if (Test-Path "scripts/publish_fx_overlay_to_analysis.py") {
    & $PY "scripts/publish_fx_overlay_to_analysis.py" --date $Date
  } else {
    WARN "missing script: scripts/publish_fx_overlay_to_analysis.py"
  }

  # ----------------------------
  # 4) Publish FX decision (optional)
  # ----------------------------
  HR "4) Publish FX decision (scripts/publish_fx_decision_to_analysis.py)"
  if (Test-Path "scripts/publish_fx_decision_to_analysis.py") {
    & $PY "scripts/publish_fx_decision_to_analysis.py" --date $Date
  } else {
    WARN "missing script: scripts/publish_fx_decision_to_analysis.py"
  }

  # ----------------------------
  # 5) Attach FX block to ViewModel (optional)
  # ----------------------------
  HR "5) Attach FX block to ViewModel (scripts/attach_fx_block_to_view_model.py)"
  if (Test-Path "scripts/attach_fx_block_to_view_model.py") {
    & $PY "scripts/attach_fx_block_to_view_model.py" --date $Date
  } else {
    WARN "missing script: scripts/attach_fx_block_to_view_model.py"
  }

  # ----------------------------
  # 6) Build Daily News Digest HTML
  # ----------------------------
  HR "6) Build Daily News Digest HTML (scripts/build_daily_news_digest.py)"
  if (Test-Path "scripts/build_daily_news_digest.py") {
    & $PY "scripts/build_daily_news_digest.py" --date $Date
  } else {
    WARN "missing script: scripts/build_daily_news_digest.py"
  }

  # ----------------------------
  # 7) Ensure daily_news dated exists (sanity)
  # ----------------------------
  HR "7) Ensure daily_news dated exists"
  $DAILY_NEWS = Join-Path $RepoRoot "data\world_politics\analysis\daily_news_$Date.json"
  if (Test-Path $DAILY_NEWS) { OK $DAILY_NEWS } else { WARN "missing: $DAILY_NEWS" }

  # ----------------------------
  # 8) Build Sentiment + normalize
  # ----------------------------
  HR "8) Build Sentiment (scripts/build_daily_sentiment.py) + normalize"
  if (Test-Path "scripts/build_daily_sentiment.py") {
    & $PY "scripts/build_daily_sentiment.py" --date $Date
  } else {
    WARN "missing script: scripts/build_daily_sentiment.py"
  }

  if (Test-Path "scripts/normalize_sentiment_latest.py") {
    & $PY "scripts/normalize_sentiment_latest.py"
  } elseif (Test-Path "scripts/normalize_sentiment_file.py") {
    & $PY "scripts/normalize_sentiment_file.py" --in "data\world_politics\analysis\sentiment_latest.json"
  } else {
    WARN "missing normalize script(s)"
  }

  # ----------------------------
  # 8.1) Patch ViewModel with sentiment summary (CRITICAL for top cards)
  # ----------------------------
  HR "8.1) Ensure ViewModel sentiment summary (scripts/ensure_view_model_sentiment_summary.py)"
  if (Test-Path "scripts/ensure_view_model_sentiment_summary.py") {
    & $PY "scripts/ensure_view_model_sentiment_summary.py" --date $Date
  } else {
    WARN "missing script: scripts/ensure_view_model_sentiment_summary.py"
  }

  # ----------------------------
  # 8.2) Build sentiment time-series CSV (sentiment.html uses this)
  # ----------------------------
  HR "8.2) Build sentiment time-series CSV (scripts/build_sentiment_timeseries_csv.py)"
  if (Test-Path "scripts/build_sentiment_timeseries_csv.py") {
    & $PY "scripts/build_sentiment_timeseries_csv.py"
  } else {
    WARN "missing script: scripts/build_sentiment_timeseries_csv.py"
  }

  # ----------------------------
  # 10) Output check
  # ----------------------------
  HR "10) Output check"
  $VM_OUT      = Join-Path $RepoRoot "data\digest\view\$Date.json"
  $VM_LATEST   = Join-Path $RepoRoot "data\digest\view_model_latest.json"
  $SENT_LATEST = Join-Path $RepoRoot "data\world_politics\analysis\sentiment_latest.json"
  $DIGEST_LATEST = Join-Path $RepoRoot "data\world_politics\analysis\daily_news_digest_latest.html"
  $SENT_CSV    = Join-Path $RepoRoot "data\world_politics\analysis\sentiment_timeseries.csv"

  if (Test-Path $VM_OUT)      { OK $VM_OUT }      else { WARN "missing: $VM_OUT" }
  if (Test-Path $VM_LATEST)   { OK $VM_LATEST }   else { WARN "missing: $VM_LATEST" }
  if (Test-Path $SENT_LATEST) { OK $SENT_LATEST } else { WARN "missing: $SENT_LATEST" }
  if (Test-Path $DIGEST_LATEST) { OK $DIGEST_LATEST } else { WARN "missing: $DIGEST_LATEST" }
  if (Test-Path $SENT_CSV)    { OK $SENT_CSV }    else { WARN "missing: $SENT_CSV" }

  HR "DONE"
  OK "Open GUI: http://127.0.0.1:8000/static/index.html?date=$Date"
  OK "Tip: Ctrl+F5 (hard refresh) if cached"
}
finally {
  Pop-Location
}
