# scripts/run_deploy_labos.ps1
# ------------------------------------------------------------
# GenesisPrediction LABOS deploy runner
# ------------------------------------------------------------
# 1) build deploy payload
# 2) verify payload exists
# 3) deploy to LABOS server
# 4) show verification URLs
# ------------------------------------------------------------

param(
    [string]$Profile = "dev"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host ""
Write-Host "===================================="
Write-Host "GenesisPrediction LABOS Deploy"
Write-Host "===================================="
Write-Host "ROOT    : $ROOT"
Write-Host "PROFILE : $Profile"
Write-Host ""

# ------------------------------------------------------------
# STEP 1: build payload
# ------------------------------------------------------------

$buildScript = Join-Path $ROOT "scripts/build_labos_deploy_payload.ps1"

Write-Host "[STEP 1] Build LABOS payload"
Write-Host $buildScript
Write-Host ""

& powershell -ExecutionPolicy Bypass -File $buildScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] payload build failed"
    exit 1
}

# ------------------------------------------------------------
# STEP 2: verify payload exists
# ------------------------------------------------------------

$payloadDir = Join-Path $ROOT "dist/labos_payload"

if (!(Test-Path $payloadDir)) {
    Write-Host ""
    Write-Host "[FAIL] payload directory not found"
    Write-Host $payloadDir
    exit 1
}

Write-Host ""
Write-Host "[OK] payload ready"
Write-Host $payloadDir
Write-Host ""

# optional local verification of prediction publish targets
$predictionLatest = Join-Path $payloadDir "data/prediction/prediction_latest.json"
$predictionHistoryIndex = Join-Path $payloadDir "data/prediction/prediction_history_index.json"
$predictionHistoryDir = Join-Path $payloadDir "data/prediction/history"

Write-Host "[VERIFY] Local payload contents"
if (Test-Path $predictionLatest) {
    Write-Host "  OK   data/prediction/prediction_latest.json"
}
else {
    Write-Host "  MISS data/prediction/prediction_latest.json"
}

if (Test-Path $predictionHistoryIndex) {
    Write-Host "  OK   data/prediction/prediction_history_index.json"
}
else {
    Write-Host "  MISS data/prediction/prediction_history_index.json"
}

if (Test-Path $predictionHistoryDir) {
    Write-Host "  OK   data/prediction/history/"
}
else {
    Write-Host "  MISS data/prediction/history/"
}

Write-Host ""

# ------------------------------------------------------------
# STEP 3: deploy
# ------------------------------------------------------------

$deployScript = Join-Path $ROOT "scripts/deploy_labos.ps1"

Write-Host "[STEP 3] Deploy to LABOS"
Write-Host $deployScript
Write-Host ""

& powershell -ExecutionPolicy Bypass -File $deployScript -Profile $Profile

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[FAIL] deploy failed"
    exit 1
}

# ------------------------------------------------------------
# STEP 4: verification URLs
# ------------------------------------------------------------

Write-Host ""
Write-Host "===================================="
Write-Host "LABOS Deploy Complete"
Write-Host "===================================="
Write-Host ""

$urls = @(
    "https://labos.soma-samui.com/static/index.html",
    "https://labos.soma-samui.com/static/overlay.html",
    "https://labos.soma-samui.com/data/world_politics/analysis/fx/fx_overlay_latest_usdthb.png",
    "https://labos.soma-samui.com/data/prediction/prediction_latest.json",
    "https://labos.soma-samui.com/data/prediction/prediction_history_index.json"
)

Write-Host "Verify URLs:"
Write-Host ""

foreach ($u in $urls) {
    Write-Host "  $u"
}

Write-Host ""
Write-Host "Done."
Write-Host ""