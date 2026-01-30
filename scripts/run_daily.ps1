# ============================================================
# GenesisPrediction v2 - Daily Pipeline Runner
# ============================================================

param(
    [string]$Date
)

# ----------------------------
# Utilities
# ----------------------------
function Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function ErrorX($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

# ----------------------------
# Resolve root & date
# ----------------------------
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $Date) {
    $Date = (Get-Date).ToString("yyyy-MM-dd")
}

Info "GenesisPrediction daily pipeline start ($Date)"

$Py = Join-Path $Root ".venv\Scripts\python.exe"

# ----------------------------
# 1) Fetcher (raw daily news)
# ----------------------------
Info "fetcher (docker compose run --rm fetcher)"
docker compose run --rm fetcher
if ($LASTEXITCODE -ne 0) {
    ErrorX "fetcher failed"
    exit 1
}

# ----------------------------
# 2) Analyzer
# ----------------------------
Info "analyzer (docker compose run --rm analyzer)"
docker compose run --rm analyzer
if ($LASTEXITCODE -ne 0) {
    ErrorX "analyzer failed"
    exit 1
}

# ----------------------------
# 3) Ensure daily_news_YYYY-MM-DD.json exists under analysis/
# ----------------------------
$rawDaily = Join-Path $Root ("data\world_politics\{0}.json" -f $Date)
$anaDaily = Join-Path $Root ("data\world_politics\analysis\daily_news_{0}.json" -f $Date)

if (Test-Path $rawDaily) {
    Copy-Item -Force $rawDaily $anaDaily
    Info "daily_news copied to analysis: $anaDaily"
} else {
    Warn "raw daily not found: $rawDaily"
}

# ----------------------------
# 4) Build daily HTML digest
# ----------------------------
Info "digest (build_daily_news_digest.py)"
& $Py "scripts/build_daily_news_digest.py" --date $Date
if ($LASTEXITCODE -ne 0) {
    ErrorX "digest build failed"
    exit 1
}

# ----------------------------
# 5) Sentiment
# ----------------------------
Info "sentiment (build_daily_sentiment.py)"
& $Py "scripts/build_daily_sentiment.py" --date $Date
if ($LASTEXITCODE -ne 0) {
    ErrorX "sentiment failed"
    exit 1
}

# ----------------------------
# 6) FX dashboard & overlay
# ----------------------------
Info "fx dashboard (fx_noise_filter_multi_thb.py)"
& $Py "scripts/fx_noise_filter_multi_thb.py"

Info "fx overlay (fx_remittance_overlay.py)"
& $Py "scripts/fx_remittance_overlay.py"

Info "fx publish (publish_fx_overlay_to_analysis.py)"
& $Py "scripts/publish_fx_overlay_to_analysis.py" --date $Date

# ----------------------------
# 7) ViewModel (GUI source of truth)
# ----------------------------
Info "viewmodel (build_digest_view_model.py)"
& $Py "scripts/build_digest_view_model.py" --date $Date
if ($LASTEXITCODE -ne 0) {
    ErrorX "viewmodel build failed"
    exit 1
}

# ----------------------------
# Done
# ----------------------------
Info "daily pipeline completed for $Date"
