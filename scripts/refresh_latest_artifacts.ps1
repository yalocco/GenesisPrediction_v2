<# 
GenesisPrediction v2
refresh_latest_artifacts.ps1

Purpose
- Ensure "latest" artifacts are refreshed into all known consumer locations:
  1) data/world_politics/analysis/*_latest.json         (source of truth for GUI data)
  2) data/world_politics/analysis/sentiment_timeseries.csv (trend source for Sentiment UI)
  3) data/digest/*                                     (legacy aliases used by older UI)
  4) dist/labos_deploy/analysis/*                       (local deploy bundle often served at /analysis/*)

Why
- Fixes UI serving stale deploy-bundle artifacts (Index/Sentiment as_of drift).
- Fixes "Sentiment Trend not enough points" when /analysis/sentiment_timeseries.csv is missing.
- Safe: copy-only, no generation, no modification of analysis content.

Run (repo root):
  powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1
#>

param(
  [Parameter(Mandatory = $false)]
  [string]$Root
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp { return (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") }
function Log([string]$msg) { Write-Host ("[{0}] {1}" -f (NowStamp), $msg) }

function Resolve-RepoRoot {
  if ($Root -and -not [string]::IsNullOrWhiteSpace($Root)) {
    return (Resolve-Path $Root).Path
  }
  if ($PSScriptRoot) {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  }
  return (Resolve-Path "..").Path
}

function Ensure-Dir([string]$path) {
  if (-not (Test-Path $path)) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
  }
}

function Copy-IfExists([string]$src, [string]$dst) {
  if (Test-Path $src) {
    Ensure-Dir (Split-Path $dst -Parent)
    Copy-Item -Force -Path $src -Destination $dst
    Log ("[OK] copy: {0} -> {1}" -f $src, $dst)
    return $true
  } else {
    Log ("[SKIP] missing: {0}" -f $src)
    return $false
  }
}

function Show-Stamp([string]$label, [string]$path) {
  if (Test-Path $path) {
    $it = Get-Item $path
    Log ("STAMP {0}: {1}  ({2} bytes)" -f $label, $it.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"), $it.Length)
  } else {
    Log ("STAMP {0}: MISSING" -f $label)
  }
}

# -----------------------------
# Main
# -----------------------------
$ROOT = Resolve-RepoRoot

$SRC_WP  = Join-Path $ROOT "data\world_politics\analysis"
$DST_DEP = Join-Path $ROOT "dist\labos_deploy\analysis"

# Legacy aliases historically used by UI
$DST_DIGEST       = Join-Path $ROOT "data\digest"
$DST_DIGEST_VIEW  = Join-Path $ROOT "data\digest\view"

Write-Host ""
Write-Host "refresh_latest_artifacts"
Write-Host ("ROOT: {0}" -f $ROOT)
Write-Host ("SRC : {0}" -f $SRC_WP)
Write-Host ("DEP : {0}" -f $DST_DEP)
Write-Host ("DIG : {0}" -f $DST_DIGEST)
Write-Host ""

# Validate source
if (-not (Test-Path $SRC_WP)) {
  throw ("Source folder not found: {0}" -f $SRC_WP)
}

# Ensure destinations exist
Ensure-Dir $DST_DEP
Ensure-Dir $DST_DIGEST
Ensure-Dir $DST_DIGEST_VIEW

# ---- Copy core "latest" artifacts ----
$src_view_model = Join-Path $SRC_WP "view_model_latest.json"
$src_summary    = Join-Path $SRC_WP "daily_summary_latest.json"
$src_sentiment  = Join-Path $SRC_WP "sentiment_latest.json"
$src_health     = Join-Path $SRC_WP "health_latest.json"
$src_ts         = Join-Path $SRC_WP "sentiment_timeseries.csv"

# 1) Deploy bundle (served as /analysis/* in many local setups)
Copy-IfExists $src_view_model (Join-Path $DST_DEP "view_model_latest.json") | Out-Null
Copy-IfExists $src_summary    (Join-Path $DST_DEP "daily_summary_latest.json") | Out-Null
Copy-IfExists $src_sentiment  (Join-Path $DST_DEP "sentiment_latest.json") | Out-Null
Copy-IfExists $src_health     (Join-Path $DST_DEP "health_latest.json") | Out-Null
Copy-IfExists $src_ts         (Join-Path $DST_DEP "sentiment_timeseries.csv") | Out-Null

# 2) Digest aliases (legacy UI paths)
Copy-IfExists $src_view_model (Join-Path $DST_DIGEST "view_model_latest.json") | Out-Null
Copy-IfExists $src_view_model (Join-Path $DST_DIGEST_VIEW "view_model_latest.json") | Out-Null

# Optional mirrors (harmless)
Copy-IfExists $src_summary   (Join-Path $DST_DIGEST "daily_summary_latest.json") | Out-Null
Copy-IfExists $src_sentiment (Join-Path $DST_DIGEST "sentiment_latest.json") | Out-Null
Copy-IfExists $src_health    (Join-Path $DST_DIGEST "health_latest.json") | Out-Null
Copy-IfExists $src_ts        (Join-Path $DST_DIGEST "sentiment_timeseries.csv") | Out-Null

# ---- Report timestamps (helps confirm stale vs fresh) ----
Log "----- TIMESTAMPS -----"
Show-Stamp "SRC view_model_latest" $src_view_model
Show-Stamp "SRC sentiment_timeseries" $src_ts
Show-Stamp "DEP view_model_latest" (Join-Path $DST_DEP "view_model_latest.json")
Show-Stamp "DEP daily_summary_latest" (Join-Path $DST_DEP "daily_summary_latest.json")
Show-Stamp "DEP sentiment_latest" (Join-Path $DST_DEP "sentiment_latest.json")
Show-Stamp "DEP sentiment_timeseries" (Join-Path $DST_DEP "sentiment_timeseries.csv")
Show-Stamp "DEP health_latest" (Join-Path $DST_DEP "health_latest.json")
Show-Stamp "DIG view_model_latest" (Join-Path $DST_DIGEST "view_model_latest.json")
Show-Stamp "DIG view/view_model_latest" (Join-Path $DST_DIGEST_VIEW "view_model_latest.json")
Show-Stamp "DIG sentiment_timeseries" (Join-Path $DST_DIGEST "sentiment_timeseries.csv")

Log "DONE refresh_latest_artifacts"
