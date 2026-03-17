param(
    [string]$Date = "",
    [switch]$Strict,
    [switch]$Guard = $true
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {

    if ($PSScriptRoot) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    # fallback（最終手段）
    $current = Get-Location
    return $current.Path
}

function Resolve-RunDate {
    param(
        [string]$InputDate
    )

    if (-not [string]::IsNullOrWhiteSpace($InputDate)) {
        return $InputDate
    }

    return (Get-Date).ToString("yyyy-MM-dd")
}

function Resolve-PythonCommand {
    param(
        [string]$RepoRoot
    )

    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        "python"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") {
            return $candidate
        }

        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Python executable not found."
}

function Ensure-Directory {
    param(
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Test-FileFreshness {
    param(
        [string]$Path
    )

    return (Test-Path $Path)
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$PythonExe,
        [string]$RepoRoot,
        [string]$ScriptPath,
        [string[]]$Arguments
    )

    Write-Host ""
    Write-Host ("[{0}] === {1} ===" -f (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss"), $Name)

    $cmdParts = @($PythonExe, $ScriptPath) + $Arguments
    Write-Host ("CMD: " + ($cmdParts -join " "))

    Push-Location $RepoRoot
    try {
        & $PythonExe $ScriptPath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

# ================================
# MAIN
# ================================

$repoRoot = Get-RepoRoot
$runDate = Resolve-RunDate -InputDate $Date
$pythonExe = Resolve-PythonCommand -RepoRoot $repoRoot

$analysisFxDir = Join-Path $repoRoot "analysis\fx"
$fxInputsPath = Join-Path $analysisFxDir "fx_inputs_latest.json"
$fxDecisionPath = Join-Path $analysisFxDir "fx_decision_latest.json"
$fxDecisionJpyThbPath = Join-Path $analysisFxDir "fx_decision_latest_jpythb.json"
$fxDecisionUsdJpyPath = Join-Path $analysisFxDir "fx_decision_latest_usdjpy.json"
$fxDecisionUsdThbPath = Join-Path $analysisFxDir "fx_decision_latest_usdthb.json"
$fxDecisionMultiPath = Join-Path $analysisFxDir "fx_decision_latest_multi.json"

Ensure-Directory -Path $analysisFxDir

Write-Host "GenesisPrediction v2 - run_daily_fx_decision"
Write-Host ("ROOT : {0}" -f $repoRoot)
Write-Host ("DATE : {0}" -f $runDate)
Write-Host ("GUARD: {0}" -f ($(if ($Guard) { "ON" } else { "OFF" })))
Write-Host ("PY   : {0}" -f $pythonExe)

# ================================
# STEP 1: FX INPUTS
# ================================

$buildArgs = @(
    "scripts/build_fx_inputs_latest.py",
    "--date", $runDate
)

if ($Strict) {
    $buildArgs += "--strict"
}

Invoke-Step `
    -Name "build_fx_inputs_latest" `
    -PythonExe $pythonExe `
    -RepoRoot $repoRoot `
    -ScriptPath $buildArgs[0] `
    -Arguments $buildArgs[1..($buildArgs.Count - 1)]

if ($Guard -and -not (Test-FileFreshness -Path $fxInputsPath)) {
    throw "Guard failed: missing $fxInputsPath"
}

# ================================
# STEP 2: FX DECISION
# ================================

Invoke-Step `
    -Name "fx_decision_engine" `
    -PythonExe $pythonExe `
    -RepoRoot $repoRoot `
    -ScriptPath "scripts/fx_decision_engine.py" `
    -Arguments @()

if ($Guard) {
    $required = @(
        $fxDecisionPath,
        $fxDecisionJpyThbPath,
        $fxDecisionUsdJpyPath,
        $fxDecisionUsdThbPath,
        $fxDecisionMultiPath
    )

    foreach ($p in $required) {
        if (-not (Test-Path $p)) {
            throw "Guard failed: missing $p"
        }
    }
}

Write-Host ""
Write-Host "[OK] FX Decision pipeline completed"