# =========================================
# GenesisPrediction LABOS Deploy
# (ENTRYPOINT - FULL REPLACEMENT / TARGET-ONLY / VERIFY-GATED)
# =========================================

param(
    [switch]$DryRun,
    [string]$BaseUrl = "https://labos.soma-samui.com",
    [int]$VerifyTimeoutSeconds = 20,
    [switch]$SkipVerify
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

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,

        [Parameter(Mandatory = $false)]
        [string[]]$ScriptArguments = @()
    )

    $pythonCommand = if (Test-Path ".venv\Scripts\python.exe") {
        ".venv\Scripts\python.exe"
    } else {
        "python"
    }

    & $pythonCommand $ScriptPath @ScriptArguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Python script failed (exit=$exitCode): $ScriptPath $($ScriptArguments -join ' ')"
    }
}

$ROOT = (Resolve-Path ".").Path
$PAYLOAD = Join-Path $ROOT "dist\labos_deploy"

Write-Host "========================================="
Write-Host " GenesisPrediction LABOS Deploy"
Write-Host " (FULL REPLACEMENT MODE / TARGET-ONLY / VERIFY-GATED)"
Write-Host "========================================="

Log "ROOT: $ROOT"
Log "MODE: $(if ($DryRun) { 'DRY RUN' } else { 'LIVE' })"
Log "BASE URL: $BaseUrl"
Log "VERIFY: $(if ($SkipVerify) { 'SKIPPED BY OPERATOR' } else { 'REQUIRED' })"

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

if ($DryRun) {
    Write-Host "========================================="
    Log "DRY RUN COMPLETE"
    Log "VERIFY SKIPPED: dry run does not update deployed artifacts"
    Write-Host "========================================="
    exit 0
}

if ($SkipVerify) {
    Write-Host "========================================="
    Log "DEPLOY COMPLETE WITHOUT VERIFY"
    Log "WARNING: deploy verification was skipped by operator"
    Write-Host "========================================="
    exit 0
}

Write-Host "-----------------------------------------"
Log "STEP 3: VERIFY DEPLOYED ARTIFACTS"
Write-Host "-----------------------------------------"

Invoke-PythonScript -ScriptPath "scripts/verify_deploy.py" -ScriptArguments @(
    "--root", $ROOT,
    "--base-url", $BaseUrl,
    "--timeout", "$VerifyTimeoutSeconds"
)

Write-Host "========================================="
Log "DEPLOY COMPLETE AND VERIFIED"
Write-Host "========================================="
