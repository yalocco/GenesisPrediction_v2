# =========================================
# GenesisPrediction LABOS Deploy
# (ENTRYPOINT - HARDENED / FIXED)
# =========================================

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[run] $msg"
}

# --------------------------------------------------
# Resolve paths
# --------------------------------------------------
$ROOT = Resolve-Path "."

$PAYLOAD = Join-Path $ROOT "dist\labos_deploy"

# --------------------------------------------------
# Header
# --------------------------------------------------
Write-Host "========================================="
Write-Host " GenesisPrediction LABOS Deploy"
Write-Host " (ENTRYPOINT - HARDENED)"
Write-Host "========================================="

Log "ROOT: $ROOT"
Log "MODE: $(if ($DryRun) { 'DRY RUN' } else { 'LIVE' })"

# --------------------------------------------------
# STEP 1: BUILD PAYLOAD
# --------------------------------------------------
Write-Host "-----------------------------------------"
Log "STEP 1: BUILD PAYLOAD"
Write-Host "-----------------------------------------"

powershell -ExecutionPolicy Bypass `
    -File "scripts/build_labos_deploy_payload.ps1" `
    -RepoRoot $ROOT

if (!(Test-Path $PAYLOAD)) {
    throw "Payload not found: $PAYLOAD"
}

# --------------------------------------------------
# STEP 2: DEPLOY
# --------------------------------------------------
Write-Host "-----------------------------------------"
Log "STEP 2: DEPLOY"
Write-Host "-----------------------------------------"

if ($DryRun) {
    powershell -ExecutionPolicy Bypass `
        -File "scripts/deploy_labos.ps1" `
        -Root $ROOT `
        -DryRun
}
else {
    powershell -ExecutionPolicy Bypass `
        -File "scripts/deploy_labos.ps1" `
        -Root $ROOT
}

Write-Host "========================================="
Write-Host "[run] LABOS DEPLOY COMPLETE"
Write-Host "========================================="