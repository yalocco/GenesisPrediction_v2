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

# build_labos_deploy_payload.ps1 の出力先と統一
$PAYLOAD = Join-Path $ROOT "dist\labos_deploy"

$KEY_PATH = "D:\AI\Projects\keys\genesisprediction-labos.pem"

$REMOTE_USER = "c3999143@www143.conoha.ne.jp"
$REMOTE_PORT = 8022
$REMOTE_PATH = "/home/c3999143/public_html/labos.soma-samui.com"

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

# --------------------------------------------------
# STEP 2: DEPLOY
# --------------------------------------------------
Write-Host "-----------------------------------------"
Log "STEP 2: DEPLOY"
Write-Host "-----------------------------------------"

if (!(Test-Path $PAYLOAD)) {
    throw "Payload not found: $PAYLOAD"
}

Write-Host "========================================="
Write-Host "[deploy] LABOS DEPLOY (STABLE)"
Write-Host "========================================="

Write-Host "[deploy] ROOT        : $ROOT"
Write-Host "[deploy] PAYLOAD     : $PAYLOAD"
Write-Host "[deploy] REMOTE      : $REMOTE_USER"
Write-Host "[deploy] PORT        : $REMOTE_PORT"
Write-Host "[deploy] REMOTE PATH : $REMOTE_PATH"
Write-Host "[deploy] KEY PATH    : $KEY_PATH"

# --------------------------------------------------
# Check .htaccess
# --------------------------------------------------
if (!(Test-Path ".htaccess")) {
    throw ".htaccess not found at repo root"
}
Write-Host "[deploy] OK root: .htaccess"

# --------------------------------------------------
# Create tar
# --------------------------------------------------
Write-Host "[deploy] creating tar..."

$tarPath = Join-Path $ROOT "dist\labos_deploy.tar.gz"

if (Test-Path $tarPath) {
    Remove-Item $tarPath -Force
}

tar -czf $tarPath -C $PAYLOAD .

Write-Host "[deploy] tar created: $tarPath"

# --------------------------------------------------
# DryRun stop
# --------------------------------------------------
if ($DryRun) {
    Write-Host "[deploy] DRY RUN STOP"
    Write-Host "========================================="
    Write-Host "[run] LABOS DEPLOY COMPLETE"
    Write-Host "========================================="
    return
}

# --------------------------------------------------
# Upload
# --------------------------------------------------
Write-Host "[deploy] uploading..."

scp -i $KEY_PATH -P $REMOTE_PORT $tarPath "${REMOTE_USER}:${REMOTE_PATH}"

# --------------------------------------------------
# Remote extract
# --------------------------------------------------
Write-Host "[deploy] extracting on server..."

ssh -i $KEY_PATH -p $REMOTE_PORT $REMOTE_USER @"
cd $REMOTE_PATH
tar -xzf labos_deploy.tar.gz
rm labos_deploy.tar.gz
"@

Write-Host "========================================="
Write-Host "[run] LABOS DEPLOY COMPLETE"
Write-Host "========================================="