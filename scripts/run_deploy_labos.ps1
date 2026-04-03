# =========================================
# GenesisPrediction LABOS Deploy
# (ENTRYPOINT - FULL REPLACEMENT / TARGET-ONLY)
# =========================================

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[run] $msg"
}

function Invoke-PowerShellScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,

        [Parameter(Mandatory = $false)]
        [string[]]$ScriptArguments = @()
    )

    & powershell -ExecutionPolicy Bypass -File $ScriptPath @ScriptArguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Script failed (exit=$exitCode): $ScriptPath $($ScriptArguments -join ' ')"
    }
}

$ROOT = (Resolve-Path ".").Path
$PAYLOAD = Join-Path $ROOT "dist\labos_deploy"

Write-Host "========================================="
Write-Host " GenesisPrediction LABOS Deploy"
Write-Host " (FULL REPLACEMENT MODE / TARGET-ONLY)"
Write-Host "========================================="

Log "ROOT: $ROOT"
Log "MODE: $(if ($DryRun) { 'DRY RUN' } else { 'LIVE' })"

Write-Host "-----------------------------------------"
Log "STEP 1: BUILD PAYLOAD"
Write-Host "-----------------------------------------"

Invoke-PowerShellScript -ScriptPath "scripts/build_labos_deploy_payload.ps1" -ScriptArguments @(
    "-RepoRoot", $ROOT
)

if (!(Test-Path $PAYLOAD)) {
    throw "Payload not found: $PAYLOAD"
}

Write-Host "-----------------------------------------"
Log "STEP 2: DEPLOY (FULL REPLACEMENT / TARGET-ONLY)"
Write-Host "-----------------------------------------"

$deployArgs = @(
    "-Root", $ROOT
)

if ($DryRun) {
    $deployArgs += "-DryRun"
}

Invoke-PowerShellScript -ScriptPath "scripts/deploy_labos.ps1" -ScriptArguments $deployArgs

Write-Host "========================================="
Log "DEPLOY COMPLETE"
Write-Host "========================================="
