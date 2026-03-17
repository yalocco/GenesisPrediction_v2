# =========================================================
# GenesisPrediction v2
# run_deploy_labos.ps1
# LABOS deploy entrypoint (HARDENED - Phase2)
# =========================================================
# RULE:
# - 人間はこのスクリプトのみ実行
# - build → deploy → verify を一括実行
# - 途中失敗は即停止
# =========================================================

param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# -----------------------------
# PATHS
# -----------------------------
$buildScript = Join-Path $Root "scripts\build_labos_deploy_payload.ps1"
$deployScript = Join-Path $Root "scripts\deploy_labos.ps1"

Write-Host "========================================="
Write-Host " GenesisPrediction LABOS Deploy"
Write-Host " (ENTRYPOINT - HARDENED)"
Write-Host "========================================="
Write-Host "[run] ROOT: $Root"

if ($DryRun) {
    Write-Host "[run] MODE: DRY RUN"
}

# -----------------------------
# CHECK SCRIPTS EXIST
# -----------------------------
if (!(Test-Path $buildScript)) {
    throw "[run][ERROR] missing build script"
}

if (!(Test-Path $deployScript)) {
    throw "[run][ERROR] missing deploy script"
}

# -----------------------------
# STEP 1: BUILD
# -----------------------------
Write-Host "-----------------------------------------"
Write-Host "[run] STEP 1: BUILD PAYLOAD"
Write-Host "-----------------------------------------"

powershell -ExecutionPolicy Bypass -File $buildScript -Root $Root

if ($LASTEXITCODE -ne 0) {
    throw "[run][ERROR] build failed"
}

# -----------------------------
# STEP 2: DEPLOY
# -----------------------------
Write-Host "-----------------------------------------"
Write-Host "[run] STEP 2: DEPLOY"
Write-Host "-----------------------------------------"

if ($DryRun) {
    powershell -ExecutionPolicy Bypass -File $deployScript -Root $Root -DryRun
} else {
    powershell -ExecutionPolicy Bypass -File $deployScript -Root $Root
}

if ($LASTEXITCODE -ne 0) {
    throw "[run][ERROR] deploy failed"
}

# -----------------------------
# DONE
# -----------------------------
Write-Host "========================================="
Write-Host "[run] LABOS DEPLOY COMPLETE"
Write-Host "========================================="