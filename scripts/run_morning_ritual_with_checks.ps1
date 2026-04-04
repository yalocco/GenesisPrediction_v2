param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Date = "",
    [switch]$SkipDeploy,
    [switch]$SkipVerify,
    [switch]$DeployDryRun,
    [string]$DeployBaseUrl = "https://labos.soma-samui.com"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$global:GP_STATUS = [ordered]@{
    ritual = "PENDING"
    post   = "PENDING"
    deploy = "PENDING"
    verify = "PENDING"
}

$global:GP_EXIT_CODE = 0

function Write-Section {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host ""
    Write-Host "[$ts] === $Message ==="
}

function Write-StepResult {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Step,

        [Parameter(Mandatory = $true)]
        [ValidateSet("OK","FAIL","SKIP","PENDING")]
        [string]$Status,

        [Parameter(Mandatory = $false)]
        [string]$Detail = ""
    )

    if ($Detail) {
        Write-Host ("[{0}] {1} - {2}" -f $Status, $Step, $Detail)
    }
    else {
        Write-Host ("[{0}] {1}" -f $Status, $Step)
    }
}

function Set-StepStatus {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("ritual","post","deploy","verify")]
        [string]$Step,

        [Parameter(Mandatory = $true)]
        [ValidateSet("OK","FAIL","SKIP","PENDING")]
        [string]$Status,

        [Parameter(Mandatory = $false)]
        [string]$Detail = ""
    )

    $global:GP_STATUS[$Step] = $Status
    Write-StepResult -Step $Step -Status $Status -Detail $Detail
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
        [object[]]$ScriptArguments = @()
    )

    & powershell -ExecutionPolicy Bypass -File $ScriptPath @ScriptArguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "Script failed with exit code ${exitCode}: $ScriptPath $($ScriptArguments -join ' ')"
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
        throw "Python script failed with exit code ${exitCode}: $ScriptPath $($ScriptArguments -join ' ')"
    }
}

function Write-FinalStatus {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ExitCode,

        [Parameter(Mandatory = $false)]
        [string]$FailureMessage = ""
    )

    Write-Section "Final Status"

    foreach ($entry in $global:GP_STATUS.GetEnumerator()) {
        Write-Host ("{0}: {1}" -f $entry.Key, $entry.Value)
    }

    if ($ExitCode -eq 0) {
        Write-Host "[DONE] Morning Ritual + Post Checks + Deploy + Verify complete"
    }
    else {
        if ($FailureMessage) {
            Write-Host ("[FAIL] {0}" -f $FailureMessage)
        }
        else {
            Write-Host "[FAIL] Pipeline failed"
        }
    }

    Write-Host ("EXIT CODE : {0}" -f $ExitCode)
}

try {
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
    try {
        Invoke-PowerShellScript -ScriptPath $MorningRitual -ScriptArguments $morningArgs
        Set-StepStatus -Step "ritual" -Status "OK"
    }
    catch {
        Set-StepStatus -Step "ritual" -Status "FAIL" -Detail $_.Exception.Message
        throw
    }

    # -----------------------------
    # 2) Run Post Ritual Checks
    #    Morning Ritual 側で vector memory を正位置 rebuild 済みのため
    #    ここでは確認専用にする
    # -----------------------------
    Write-Section "Run Post Ritual Checks"

    $postArgs = @("-AutoRebuildVectorMemory", $false)
    Write-Host ("CMD: powershell -ExecutionPolicy Bypass -File {0} {1}" -f $PostChecks, ($postArgs -join " "))
    try {
        Invoke-PowerShellScript -ScriptPath $PostChecks -ScriptArguments $postArgs
        Set-StepStatus -Step "post" -Status "OK"
    }
    catch {
        Set-StepStatus -Step "post" -Status "FAIL" -Detail $_.Exception.Message
        throw
    }

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
        try {
            Invoke-PowerShellScript -ScriptPath $DeployScript -ScriptArguments $deployArgs
            Set-StepStatus -Step "deploy" -Status "OK"
        }
        catch {
            Set-StepStatus -Step "deploy" -Status "FAIL" -Detail $_.Exception.Message
            throw
        }
    }
    else {
        Write-Section "Skip LABOS Deploy"
        Set-StepStatus -Step "deploy" -Status "SKIP" -Detail "Deploy step skipped"
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
        try {
            Invoke-PythonScript -PythonExe $PythonExe -ScriptPath $VerifyScript -ScriptArguments $verifyArgs
            Set-StepStatus -Step "verify" -Status "OK"
        }
        catch {
            Set-StepStatus -Step "verify" -Status "FAIL" -Detail $_.Exception.Message
            throw
        }
    }
    else {
        Write-Section "Skip Deploy Verification"
        Set-StepStatus -Step "verify" -Status "SKIP" -Detail "Verification step skipped"
    }

    # -----------------------------
    # Done
    # -----------------------------
    $global:GP_EXIT_CODE = 0
    Write-FinalStatus -ExitCode $global:GP_EXIT_CODE
    exit $global:GP_EXIT_CODE
}
catch {
    $global:GP_EXIT_CODE = 1
    Write-FinalStatus -ExitCode $global:GP_EXIT_CODE -FailureMessage $_.Exception.Message
    exit $global:GP_EXIT_CODE
}
