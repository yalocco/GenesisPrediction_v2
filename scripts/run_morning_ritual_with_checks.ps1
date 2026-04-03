param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Date = "",
    [switch]$SkipDeploy,
    [switch]$SkipVerify,
    [switch]$DeployDryRun,
    [string]$DeployBaseUrl = "https://labos.soma-samui.com"
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host ""
    Write-Host "[$ts] === $Message ==="
}

function Resolve-PythonCommand {
    param([string]$RepoRoot)

    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        "python"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") { return $candidate }
        if (Test-Path $candidate) { return $candidate }
    }

    throw "Python executable not found."
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
        throw "Script failed with exit code $exitCode: $ScriptPath $($ScriptArguments -join ' ')"
    }
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe,

        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,

        [Parameter(Mandatory = $false)]
        [string[]]$ScriptArguments = @()
    )

    & $PythonExe $ScriptPath @ScriptArguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "Python script failed with exit code $exitCode: $ScriptPath $($ScriptArguments -join ' ')"
    }
}

# -----------------------------
# Resolve paths
# -----------------------------
$Root = (Resolve-Path $Root).Path
$MorningRitual = Join-Path $Root "scripts\run_morning_ritual.ps1"
$PostChecks = Join-Path $Root "scripts\run_post_ritual_checks.ps1"
$DeployScript = Join-Path $Root "scripts\run_deploy_labos.ps1"
$VerifyScript = Join-Path $Root "scripts\verify_deploy.py"
$PythonExe = Resolve-PythonCommand -RepoRoot $Root

if (-not (Test-Path $MorningRitual)) {
    throw "Missing script: $MorningRitual"
}

if (-not (Test-Path $PostChecks)) {
    throw "Missing script: $PostChecks"
}

if (-not $SkipDeploy -and -not (Test-Path $DeployScript)) {
    throw "Missing script: $DeployScript"
}

if (-not $SkipVerify -and -not (Test-Path $VerifyScript)) {
    throw "Missing script: $VerifyScript"
}

Write-Host "GenesisPrediction - Morning Ritual (with Post Checks + Deploy Verify)"
Write-Host "ROOT : $Root"
Write-Host "DEPLOY BASE URL : $DeployBaseUrl"

if ($Date -ne "") {
    Write-Host "DATE : $Date"
}

Write-Host ("SKIP DEPLOY : {0}" -f ($SkipDeploy.IsPresent))
Write-Host ("SKIP VERIFY : {0}" -f ($SkipVerify.IsPresent))
Write-Host ("DEPLOY DRY RUN : {0}" -f ($DeployDryRun.IsPresent))

# -----------------------------
# 1) Run original Morning Ritual
# -----------------------------
Write-Section "Run Morning Ritual"

$morningArgs = @()
if ($Date -ne "") {
    $morningArgs += @("-Date", $Date)
}

Write-Host ("CMD: powershell -ExecutionPolicy Bypass -File {0} {1}" -f $MorningRitual, ($morningArgs -join " "))
Invoke-PowerShellScript -ScriptPath $MorningRitual -ScriptArguments $morningArgs

# -----------------------------
# 2) Run Post Ritual Checks
# -----------------------------
Write-Section "Run Post Ritual Checks"

Write-Host "CMD: powershell -ExecutionPolicy Bypass -File $PostChecks"
Invoke-PowerShellScript -ScriptPath $PostChecks

# -----------------------------
# 3) Deploy to LABOS
# -----------------------------
if (-not $SkipDeploy) {
    Write-Section "Run LABOS Deploy"

    $deployArgs = @()
    if ($DeployDryRun) {
        $deployArgs += "-DryRun"
    }

    Write-Host ("CMD: powershell -ExecutionPolicy Bypass -File {0} {1}" -f $DeployScript, ($deployArgs -join " "))
    Invoke-PowerShellScript -ScriptPath $DeployScript -ScriptArguments $deployArgs
}
else {
    Write-Section "Skip LABOS Deploy"
    Write-Host "[SKIP] Deploy step skipped"
}

# -----------------------------
# 4) Verify deployed artifacts
# -----------------------------
if (-not $SkipVerify) {
    Write-Section "Run Deploy Verification"

    $verifyArgs = @(
        "--root", $Root,
        "--base-url", $DeployBaseUrl
    )

    Write-Host ("CMD: {0} {1} {2}" -f $PythonExe, $VerifyScript, ($verifyArgs -join " "))
    Invoke-PythonScript -PythonExe $PythonExe -ScriptPath $VerifyScript -ScriptArguments $verifyArgs
}
else {
    Write-Section "Skip Deploy Verification"
    Write-Host "[SKIP] Verification step skipped"
}

# -----------------------------
# Done
# -----------------------------
Write-Section "All Complete"

Write-Host "[DONE] Morning Ritual + Post Checks + Deploy + Verify complete"
exit 0
