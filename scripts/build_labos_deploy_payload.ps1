# =========================================================
# GenesisPrediction v2
# LABOS Deploy Payload Builder (FINAL - Phase4 Integrated)
# =========================================================

param(
    [string]$RepoRoot = ".",
    [string]$OutDir = "dist/labos_deploy"
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[build_labos_deploy_payload] $msg"
}

# ---------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------
$root = Resolve-Path $RepoRoot
$out  = Join-Path $root $OutDir

Log "ROOT : $root"
Log "OUT  : $out"

# Clean
if (Test-Path $out) {
    Remove-Item -Recurse -Force $out
}
New-Item -ItemType Directory -Path $out | Out-Null

# ---------------------------------------------------------
# 1. Copy static UI
# ---------------------------------------------------------
$staticSrc = Join-Path $root "app/static"
$staticDst = Join-Path $out  "static"

Log "Copy static..."
Copy-Item -Recurse -Force $staticSrc $staticDst

# ---------------------------------------------------------
# 2. Prepare data directory
# ---------------------------------------------------------
$dataDst = Join-Path $out "data"
New-Item -ItemType Directory -Path $dataDst | Out-Null

# ---------------------------------------------------------
# 3. Copy world / digest data (existing behavior)
# ---------------------------------------------------------
$dataSrc = Join-Path $root "data"

if (Test-Path $dataSrc) {
    Log "Copy data..."
    Copy-Item -Recurse -Force $dataSrc\* $dataDst
}

# ---------------------------------------------------------
# 4. 🔥 CRITICAL: Copy prediction from analysis → data
# ---------------------------------------------------------
$analysisPrediction = Join-Path $root "analysis/prediction"
$dataPredictionDst  = Join-Path $dataDst "prediction"

if (!(Test-Path $analysisPrediction)) {
    throw "analysis/prediction not found"
}

Log "Copy prediction (analysis → data)..."
New-Item -ItemType Directory -Path $dataPredictionDst -Force | Out-Null

Copy-Item -Recurse -Force "$analysisPrediction\*" $dataPredictionDst

# ---------------------------------------------------------
# 5. Required files check
# ---------------------------------------------------------
$required = @(
    "trend_latest.json",
    "signal_latest.json",
    "early_warning_latest.json",
    "scenario_latest.json",
    "prediction_latest.json",
    "prediction_history_index.json"
)

foreach ($f in $required) {
    $p = Join-Path $dataPredictionDst $f
    if (!(Test-Path $p)) {
        throw "Missing required file: $p"
    }
}

Log "All required prediction files OK"

# ---------------------------------------------------------
# 6. History check
# ---------------------------------------------------------
$historyDir = Join-Path $dataPredictionDst "history"

if (!(Test-Path $historyDir)) {
    Log "[WARN] history directory not found"
} else {
    $count = (Get-ChildItem $historyDir -Recurse -Filter prediction.json | Measure-Object).Count
    Log "History snapshots: $count"
}

# ---------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------
Log "Payload build complete"
Log "OUTPUT: $out"