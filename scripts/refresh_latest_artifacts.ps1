<#
GenesisPrediction v2
refresh_latest_artifacts.ps1

Purpose
- Refresh "latest" artifacts into known consumer locations without mixing responsibilities.
- World artifacts stay world.
- Digest artifacts stay digest.
- FX artifacts are NOT generated or overwritten here; only timestamps are reported.

Rules
- analysis/data sources are the truth for runtime inputs.
- This script is copy-only.
- This script must NOT convert world view_model into digest view_model.
- Fallback is for UI continuity only, not a replacement for formal latest artifacts.

Current policy
1) World source
   - data/world_politics/analysis/daily_summary_latest.json
   - data/world_politics/analysis/sentiment_latest.json
   - data/world_politics/analysis/health_latest.json
   - data/world_politics/analysis/sentiment_timeseries.csv
   - data/world_politics/analysis/world_view_model_latest.json (preferred if exists)
   - data/world_politics/analysis/view_model_latest.json       (legacy world source only)

2) Digest source
   - data/digest/view_model_latest.json   <-- formal digest latest

3) Legacy digest aliases
   - data/digest/view/view_model_latest.json

4) Deploy bundle mirrors
   - dist/labos_deploy/analysis/*
   - NOTE:
     /analysis/view_model_latest.json in deploy bundle is fed from DIGEST latest,
     not from world view model.

5) FX diagnostics
   - Formal published overlays are checked under data/world_politics/analysis
   - Legacy / working files under data/fx are reported separately as reference only
   - This script does not generate or publish FX artifacts

Run (repo root):
  powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1
#>

param(
  [Parameter(Mandatory = $false)]
  [string]$Root
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp {
  return (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
}

function Log([string]$msg) {
  Write-Host ("[{0}] {1}" -f (NowStamp), $msg)
}

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

function First-ExistingFile([string[]]$paths) {
  foreach ($p in $paths) {
    if (Test-Path $p) {
      return $p
    }
  }
  return $null
}

# -----------------------------
# Main
# -----------------------------
$ROOT = Resolve-RepoRoot

$SRC_WORLD   = Join-Path $ROOT "data\world_politics\analysis"
$SRC_DIGEST  = Join-Path $ROOT "data\digest"
$SRC_FX      = Join-Path $ROOT "data\fx"

$DST_DEP_ANALYSIS = Join-Path $ROOT "dist\labos_deploy\analysis"

# legacy digest alias historically used by older UI
$DST_DIGEST_VIEW  = Join-Path $ROOT "data\digest\view"

Write-Host ""
Write-Host "refresh_latest_artifacts"
Write-Host ("ROOT   : {0}" -f $ROOT)
Write-Host ("WORLD  : {0}" -f $SRC_WORLD)
Write-Host ("DIGEST : {0}" -f $SRC_DIGEST)
Write-Host ("FX     : {0}" -f $SRC_FX)
Write-Host ("DEP    : {0}" -f $DST_DEP_ANALYSIS)
Write-Host ""

if (-not (Test-Path $SRC_WORLD)) {
  throw ("World source folder not found: {0}" -f $SRC_WORLD)
}

if (-not (Test-Path $SRC_DIGEST)) {
  throw ("Digest source folder not found: {0}" -f $SRC_DIGEST)
}

Ensure-Dir $DST_DEP_ANALYSIS
Ensure-Dir $DST_DIGEST_VIEW

# -----------------------------
# Source paths
# -----------------------------
$src_world_summary   = Join-Path $SRC_WORLD "daily_summary_latest.json"
$src_world_sentiment = Join-Path $SRC_WORLD "sentiment_latest.json"
$src_world_health    = Join-Path $SRC_WORLD "health_latest.json"
$src_world_ts        = Join-Path $SRC_WORLD "sentiment_timeseries.csv"

# World view model:
# preferred formal name -> world_view_model_latest.json
# legacy source name    -> view_model_latest.json
$src_world_view_candidates = @(
  (Join-Path $SRC_WORLD "world_view_model_latest.json"),
  (Join-Path $SRC_WORLD "view_model_latest.json")
)
$src_world_view = First-ExistingFile $src_world_view_candidates

# Digest formal latest
$src_digest_view = Join-Path $SRC_DIGEST "view_model_latest.json"

# -----------------------------
# 1) Deploy bundle mirrors
# -----------------------------
Log "----- DEPLOY MIRROR: WORLD -----"
Copy-IfExists $src_world_summary   (Join-Path $DST_DEP_ANALYSIS "daily_summary_latest.json") | Out-Null
Copy-IfExists $src_world_sentiment (Join-Path $DST_DEP_ANALYSIS "sentiment_latest.json") | Out-Null
Copy-IfExists $src_world_health    (Join-Path $DST_DEP_ANALYSIS "health_latest.json") | Out-Null
Copy-IfExists $src_world_ts        (Join-Path $DST_DEP_ANALYSIS "sentiment_timeseries.csv") | Out-Null

if ($src_world_view) {
  Copy-IfExists $src_world_view (Join-Path $DST_DEP_ANALYSIS "world_view_model_latest.json") | Out-Null
} else {
  Log "[SKIP] world view model missing: neither world_view_model_latest.json nor legacy view_model_latest.json found"
}

Log "----- DEPLOY MIRROR: DIGEST -----"
Copy-IfExists $src_digest_view (Join-Path $DST_DEP_ANALYSIS "view_model_latest.json") | Out-Null
Copy-IfExists $src_digest_view (Join-Path $DST_DEP_ANALYSIS "digest_view_model_latest.json") | Out-Null

# -----------------------------
# 2) Legacy digest aliases
# -----------------------------
Log "----- LEGACY DIGEST ALIAS -----"
Copy-IfExists $src_digest_view (Join-Path $DST_DIGEST_VIEW "view_model_latest.json") | Out-Null

# -----------------------------
# 3) Stale cleanup policy
# -----------------------------
Log "----- STALE CLEANUP -----"
if (-not (Test-Path $src_digest_view)) {
  Log "[WARN] digest formal latest is missing: data/digest/view_model_latest.json"
  Log "[WARN] deploy generic view_model_latest.json was NOT refreshed from world fallback"
}

# -----------------------------
# 4) Timestamp report
# -----------------------------
Log "----- TIMESTAMPS: WORLD -----"
Show-Stamp "WORLD daily_summary_latest"   $src_world_summary
Show-Stamp "WORLD sentiment_latest"       $src_world_sentiment
Show-Stamp "WORLD health_latest"          $src_world_health
Show-Stamp "WORLD sentiment_timeseries"   $src_world_ts
if ($src_world_view) {
  Show-Stamp "WORLD view model source"    $src_world_view
} else {
  Log "STAMP WORLD view model source: MISSING"
}

Log "----- TIMESTAMPS: DIGEST -----"
Show-Stamp "DIGEST view_model_latest"     $src_digest_view
Show-Stamp "DIGEST alias view/view_model_latest" (Join-Path $DST_DIGEST_VIEW "view_model_latest.json")

Log "----- TIMESTAMPS: DEPLOY -----"
Show-Stamp "DEP view_model_latest"        (Join-Path $DST_DEP_ANALYSIS "view_model_latest.json")
Show-Stamp "DEP digest_view_model_latest" (Join-Path $DST_DEP_ANALYSIS "digest_view_model_latest.json")
Show-Stamp "DEP world_view_model_latest"  (Join-Path $DST_DEP_ANALYSIS "world_view_model_latest.json")
Show-Stamp "DEP daily_summary_latest"     (Join-Path $DST_DEP_ANALYSIS "daily_summary_latest.json")
Show-Stamp "DEP sentiment_latest"         (Join-Path $DST_DEP_ANALYSIS "sentiment_latest.json")
Show-Stamp "DEP sentiment_timeseries"     (Join-Path $DST_DEP_ANALYSIS "sentiment_timeseries.csv")
Show-Stamp "DEP health_latest"            (Join-Path $DST_DEP_ANALYSIS "health_latest.json")

# -----------------------------
# 5) FX diagnostics only
# -----------------------------
Log "----- FX DIAGNOSTICS: FORMAL PUBLISHED OVERLAYS -----"
# Formal published overlays now live under world analysis.
$fx_pub_jpythb_latest = Join-Path $SRC_WORLD "fx_jpy_thb_overlay.png"
$fx_pub_usdjpy_latest = Join-Path $SRC_WORLD "fx_jpy_usd_overlay.png"
$fx_pub_jpythb_ptr    = Join-Path $SRC_WORLD "fx_jpy_thb_overlay_latest.txt"
$fx_pub_usdjpy_ptr    = Join-Path $SRC_WORLD "fx_jpy_usd_overlay_latest.txt"
$fx_pub_legacy_thb    = Join-Path $SRC_WORLD "jpy_thb_remittance_overlay.png"
$fx_pub_legacy_ptr    = Join-Path $SRC_WORLD "fx_overlay_latest.txt"

Show-Stamp "FX published latest JPYTHB"        $fx_pub_jpythb_latest
Show-Stamp "FX published latest USDJPY"        $fx_pub_usdjpy_latest
Show-Stamp "FX published pointer JPYTHB"       $fx_pub_jpythb_ptr
Show-Stamp "FX published pointer USDJPY"       $fx_pub_usdjpy_ptr
Show-Stamp "FX published legacy THB overlay"   $fx_pub_legacy_thb
Show-Stamp "FX published legacy pointer"       $fx_pub_legacy_ptr

Log "----- FX DIAGNOSTICS: WORKING / LEGACY FX FILES -----"
# These are reference-only working files under data/fx.
$fx_work_jpythb_overlay = Join-Path $SRC_FX "fx_jpy_thb_overlay.png"
$fx_work_usdjpy_overlay = Join-Path $SRC_FX "fx_jpy_usd_overlay.png"
$fx_work_multi_overlay  = Join-Path $SRC_FX "fx_multi_overlay.png"
$fx_work_remit_overlay  = Join-Path $SRC_FX "jpy_thb_remittance_overlay.png"

Show-Stamp "FX working overlay JPYTHB"         $fx_work_jpythb_overlay
Show-Stamp "FX working overlay USDJPY"         $fx_work_usdjpy_overlay
Show-Stamp "FX working overlay MULTI"          $fx_work_multi_overlay
Show-Stamp "FX working remittance overlay"     $fx_work_remit_overlay

Log "----- FX DIAGNOSTICS: OPTIONAL LEGACY LATEST ALIASES -----"
# Old alias names may still exist in some environments, but are no longer treated as formal truth.
$fx_legacy_latest_jpythb = Join-Path $SRC_FX "fx_overlay_latest_jpythb.png"
$fx_legacy_latest_usdjpy = Join-Path $SRC_FX "fx_overlay_latest_usdjpy.png"
$fx_legacy_latest_usdthb = Join-Path $SRC_FX "fx_overlay_latest_usdthb.png"
$fx_legacy_latest_multi  = Join-Path $SRC_FX "fx_overlay_multi_latest.png"

Show-Stamp "FX legacy latest alias JPYTHB"     $fx_legacy_latest_jpythb
Show-Stamp "FX legacy latest alias USDJPY"     $fx_legacy_latest_usdjpy
Show-Stamp "FX legacy latest alias USDTHB"     $fx_legacy_latest_usdthb
Show-Stamp "FX legacy latest alias MULTI"      $fx_legacy_latest_multi

Log "----- FX DIAGNOSTICS: DECISION JSON -----"
$fx_decision_common = Join-Path $SRC_FX "fx_decision_latest.json"
$fx_decision_jpythb = Join-Path $SRC_FX "fx_decision_latest_jpythb.json"
$fx_decision_usdjpy = Join-Path $SRC_FX "fx_decision_latest_usdjpy.json"
$fx_decision_usdthb = Join-Path $SRC_FX "fx_decision_latest_usdthb.json"
$fx_decision_multi  = Join-Path $SRC_FX "fx_decision_latest_multi.json"

Show-Stamp "FX decision latest common"         $fx_decision_common
Show-Stamp "FX decision latest JPYTHB"         $fx_decision_jpythb
Show-Stamp "FX decision latest USDJPY"         $fx_decision_usdjpy
Show-Stamp "FX decision latest USDTHB"         $fx_decision_usdthb
Show-Stamp "FX decision latest MULTI"          $fx_decision_multi

Log "DONE refresh_latest_artifacts"