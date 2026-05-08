# =========================================
# GenesisPrediction LABOS Deploy
# (ENTRYPOINT - FULL REPLACEMENT / TARGET-ONLY / VERIFY-GATED)
# =========================================

param(
    [switch]$DryRun,
    [string]$BaseUrl = "https://labos.soma-samui.com",
    [int]$VerifyTimeoutSeconds = 20,
    [switch]$SkipVerify,
    [string]$KeyPath
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[run] $msg"
}

function Resolve-PowerShellCommand {
    if ($PSVersionTable.PSEdition -eq "Core") {
        $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
        if ($null -ne $pwsh) {
            return $pwsh.Source
        }
    }

    $windowsPowerShell = Get-Command powershell -ErrorAction SilentlyContinue
    if ($null -ne $windowsPowerShell) {
        return $windowsPowerShell.Source
    }

    $fallbackPwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($null -ne $fallbackPwsh) {
        return $fallbackPwsh.Source
    }

    throw "PowerShell executable not found. Checked pwsh and powershell."
}

function Invoke-PowerShellScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,

        [Parameter(Mandatory = $false)]
        [string[]]$ScriptArguments = @()
    )

    $psCommand = Resolve-PowerShellCommand

    Write-Host "[run] PowerShell command: $psCommand"
    Write-Host "[run] PowerShell script : $ScriptPath"

    & $psCommand -ExecutionPolicy Bypass -File $ScriptPath @ScriptArguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Script failed (exit=$exitCode): $ScriptPath $($ScriptArguments -join ' ')"
    }
}

function Resolve-PythonCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $windowsVenvPython = Join-Path (Join-Path $RepoRoot ".venv") "Scripts\python.exe"
    $posixVenvPython = Join-Path (Join-Path $RepoRoot ".venv") "bin/python"

    if (Test-Path $windowsVenvPython) {
        return $windowsVenvPython
    }

    if (Test-Path $posixVenvPython) {
        return $posixVenvPython
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        return $python.Source
    }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($null -ne $python3) {
        return $python3.Source
    }

    throw "Python executable not found. Checked .venv, python, and python3."
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,

        [Parameter(Mandatory = $false)]
        [string[]]$ScriptArguments = @()
    )

    $pythonCommand = Resolve-PythonCommand -RepoRoot $ROOT

    Write-Host "[run] Python command: $pythonCommand"
    Write-Host "[run] Python script : $ScriptPath"

    & $pythonCommand $ScriptPath @ScriptArguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Python script failed (exit=$exitCode): $ScriptPath $($ScriptArguments -join ' ')"
    }
}

$ROOT = (Resolve-Path ".").Path
$PAYLOAD = Join-Path (Join-Path $ROOT "dist") "labos_deploy"

$buildPayloadScript = Join-Path (Join-Path $ROOT "scripts") "build_labos_deploy_payload.ps1"
$deployScript = Join-Path (Join-Path $ROOT "scripts") "deploy_labos.ps1"
$verifyScript = Join-Path (Join-Path $ROOT "scripts") "verify_deploy.py"

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

Invoke-PowerShellScript -ScriptPath $buildPayloadScript -ScriptArguments @(
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

Invoke-PowerShellScript -ScriptPath $deployScript -ScriptArguments $deployArgs

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

Invoke-PythonScript -ScriptPath $verifyScript -ScriptArguments @(
    "--root", $ROOT,
    "--base-url", $BaseUrl,
    "--timeout", "$VerifyTimeoutSeconds"
)

Write-Host "========================================="
Log "DEPLOY COMPLETE AND VERIFIED"
Write-Host "========================================="
