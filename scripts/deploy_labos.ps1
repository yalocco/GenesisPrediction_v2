# =========================================================
# GenesisPrediction v2
# deploy_labos.ps1
# LABOS deploy script (HARDENED - STABLE)
# =========================================================

param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$RemotePath = "/home/c3999143/public_html/labos.soma-samui.com",
    [string]$HostName = "www143.conoha.ne.jp",
    [string]$UserName = "c3999143",
    [int]$Port = 8022,
    [string]$KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$payload = Join-Path $Root "dist\labos_payload"
$manifest = Join-Path $payload "manifest.json"
$tmpTar = Join-Path $Root "dist\labos_payload.tar.gz"

$remoteTarget = "${UserName}@${HostName}"
$remoteTarPath = "$RemotePath/payload.tar.gz"

Write-Host "========================================="
Write-Host "[deploy] LABOS DEPLOY (STABLE)"
Write-Host "========================================="
Write-Host "[deploy] ROOT        : $Root"
Write-Host "[deploy] PAYLOAD     : $payload"
Write-Host "[deploy] REMOTE      : $remoteTarget"
Write-Host "[deploy] PORT        : $Port"
Write-Host "[deploy] REMOTE PATH : $RemotePath"
Write-Host "[deploy] KEY PATH    : $KeyPath"

# -----------------------------
# PRECHECK
# -----------------------------
if (!(Test-Path $payload)) {
    throw "[deploy][ERROR] payload missing: $payload"
}

if (!(Test-Path $manifest)) {
    throw "[deploy][ERROR] manifest missing: $manifest"
}

if (!(Test-Path $KeyPath)) {
    throw "[deploy][ERROR] key missing: $KeyPath"
}

$requiredRootFiles = @(
    ".htaccess"
)

foreach ($file in $requiredRootFiles) {
    $path = Join-Path $payload $file
    if (!(Test-Path $path)) {
        throw "[deploy][ERROR] required root file missing in payload: $file"
    }
    Write-Host "[deploy] OK root: $file"
}

# -----------------------------
# TAR
# -----------------------------
Write-Host "[deploy] creating tar..."

if (Test-Path $tmpTar) {
    Remove-Item $tmpTar -Force
}

& tar -czf $tmpTar -C $payload .

if ($LASTEXITCODE -ne 0) {
    throw "[deploy][ERROR] tar creation failed"
}

if (!(Test-Path $tmpTar)) {
    throw "[deploy][ERROR] tar failed: $tmpTar"
}

Write-Host "[deploy] tar created: $tmpTar"

# -----------------------------
# DRY RUN
# -----------------------------
if ($DryRun) {
    Write-Host "[deploy] DRY RUN STOP"
    return
}

# -----------------------------
# UPLOAD
# -----------------------------
Write-Host "[deploy] uploading..."

& scp -i $KeyPath -P $Port $tmpTar "${remoteTarget}:${remoteTarPath}"

if ($LASTEXITCODE -ne 0) {
    throw "[deploy][ERROR] upload failed"
}

# -----------------------------
# REMOTE DEPLOY
# -----------------------------
Write-Host "[deploy] remote deploy..."

$cmd = "cd $RemotePath && rm -rf backup && if [ -d current ]; then mv current backup; fi && mkdir -p current && tar -xzf payload.tar.gz -C current && test -f current/.htaccess"

& ssh -i $KeyPath -p $Port $remoteTarget $cmd

if ($LASTEXITCODE -ne 0) {
    throw "[deploy][ERROR] remote deploy failed"
}

# -----------------------------
# VERIFY
# -----------------------------
Write-Host "[deploy] verify..."

$verify = "test -f $RemotePath/current/.htaccess && test -f $RemotePath/current/data/prediction/prediction_latest.json"

& ssh -i $KeyPath -p $Port $remoteTarget $verify

if ($LASTEXITCODE -ne 0) {
    throw "[deploy][ERROR] verify failed"
}

Write-Host "-----------------------------------------"
Write-Host "[deploy] SUCCESS"
Write-Host "-----------------------------------------"