param(
    [string]$Date = "",
    [switch]$SkipMain,
    [switch]$SkipPrediction,
    [switch]$SkipFx,
    [switch]$SkipHealth,
    [switch]$SkipRefresh,
    [switch]$Guard = $true
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    if ($PSScriptRoot) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    return (Get-Location).Path
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

function Invoke-PowerShellScript {
    param(
        [string]$Name,
        [string]$RepoRoot,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    Write-Host ""
    Write-Host ("[{0}] === {1} ===" -f (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss"), $Name)

    $cmdParts = @(
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", $ScriptPath
    ) + $Arguments

    Write-Host ("CMD: " + ($cmdParts -join " "))

    Push-Location $RepoRoot
    try {
        & powershell -ExecutionPolicy Bypass -File $ScriptPath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-PythonScript {
    param(
        [string]$Name,
        [string]$RepoRoot,
        [string]$PythonExe,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
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

function Assert-PathExists {
    param(
        [string]$Path,
        [string]$Message = ""
    )

    if (-not (Test-Path $Path)) {
        if ([string]::IsNullOrWhiteSpace($Message)) {
            throw "Missing required path: $Path"
        }
        throw $Message
    }
}

$repoRoot = Get-RepoRoot
$runDate = Resolve-RunDate -InputDate $Date
$pythonExe = Resolve-PythonCommand -RepoRoot $repoRoot

Write-Host "Morning Ritual (single entrypoint)"
Write-Host ("ROOT        : {0}" -f $repoRoot)
Write-Host ("DATE        : {0}" -f $runDate)
Write-Host ("GUARD       : {0}" -f ($(if ($Guard) { "ON" } else { "OFF" })))
Write-Host ("MAIN        : {0}" -f ($(if ($SkipMain) { "SKIP" } else { "RUN" })))
Write-Host ("PREDICTION  : {0}" -f ($(if ($SkipPrediction) { "SKIP" } else { "RUN" })))
Write-Host ("FX          : {0}" -f ($(if ($SkipFx) { "SKIP" } else { "RUN" })))
Write-Host ("HEALTH      : {0}" -f ($(if ($SkipHealth) { "SKIP" } else { "RUN" })))
Write-Host ("REFRESH     : {0}" -f ($(if ($SkipRefresh) { "SKIP" } else { "RUN" })))
Write-Host ("PYTHON      : {0}" -f $pythonExe)

$mainWorldSummary = Join-Path $repoRoot "analysis\world_politics\daily_summary_latest.json"
$predictionLatest = Join-Path $repoRoot "analysis\prediction\prediction_latest.json"
$fxDecisionLatest = Join-Path $repoRoot "analysis\fx\fx_decision_latest.json"
$healthLatest = Join-Path $repoRoot "analysis\health_latest.json"

# ============================================================
# 1) Main lane
# ============================================================
if (-not $SkipMain) {
    Invoke-PowerShellScript `
        -Name "run_daily_with_publish" `
        -RepoRoot $repoRoot `
        -ScriptPath "scripts/run_daily_with_publish.ps1" `
        -Arguments @("-Date", $runDate)

    if ($Guard) {
        Assert-PathExists `
            -Path $mainWorldSummary `
            -Message "Guard failed after main lane: missing $mainWorldSummary"
    }
}

# ============================================================
# 2) Prediction lane
# ============================================================
if (-not $SkipPrediction) {
    Invoke-PythonScript `
        -Name "trend_engine" `
        -RepoRoot $repoRoot `
        -PythonExe $pythonExe `
        -ScriptPath "scripts/trend_engine.py"

    Invoke-PythonScript `
        -Name "signal_engine" `
        -RepoRoot $repoRoot `
        -PythonExe $pythonExe `
        -ScriptPath "scripts/signal_engine.py"

    Invoke-PythonScript `
        -Name "scenario_engine" `
        -RepoRoot $repoRoot `
        -PythonExe $pythonExe `
        -ScriptPath "scripts/scenario_engine.py"

    Invoke-PythonScript `
        -Name "prediction_engine" `
        -RepoRoot $repoRoot `
        -PythonExe $pythonExe `
        -ScriptPath "scripts/prediction_engine.py"

    if ($Guard) {
        Assert-PathExists `
            -Path $predictionLatest `
            -Message "Guard failed after prediction lane: missing $predictionLatest"
    }
}

# ============================================================
# 3) FX lane
# ============================================================
if (-not $SkipFx) {
    Invoke-PowerShellScript `
        -Name "run_daily_fx_rates" `
        -RepoRoot $repoRoot `
        -ScriptPath "scripts/run_daily_fx_rates.ps1" `
        -Arguments @("-Date", $runDate)

    Invoke-PowerShellScript `
        -Name "run_daily_fx_inputs" `
        -RepoRoot $repoRoot `
        -ScriptPath "scripts/run_daily_fx_inputs.ps1" `
        -Arguments @("-Date", $runDate)

    Invoke-PowerShellScript `
        -Name "run_daily_fx_overlay" `
        -RepoRoot $repoRoot `
        -ScriptPath "scripts/run_daily_fx_overlay.ps1" `
        -Arguments @("-Date", $runDate)

    Invoke-PowerShellScript `
        -Name "run_daily_fx_decision" `
        -RepoRoot $repoRoot `
        -ScriptPath "scripts/run_daily_fx_decision.ps1" `
        -Arguments @("-Date", $runDate, "-Strict")

    if ($Guard) {
        Assert-PathExists `
            -Path $fxDecisionLatest `
            -Message "Guard failed after FX lane: missing $fxDecisionLatest"
    }
}

# ============================================================
# 4) Health lane
# ============================================================
if (-not $SkipHealth) {
    Invoke-PythonScript `
        -Name "build_data_health" `
        -RepoRoot $repoRoot `
        -PythonExe $pythonExe `
        -ScriptPath "scripts/build_data_health.py"

    if ($Guard) {
        Assert-PathExists `
            -Path $healthLatest `
            -Message "Guard failed after health lane: missing $healthLatest"
    }
}

# ============================================================
# 5) Refresh lane
# ============================================================
if (-not $SkipRefresh) {
    Invoke-PowerShellScript `
        -Name "refresh_latest_artifacts" `
        -RepoRoot $repoRoot `
        -ScriptPath "scripts/refresh_latest_artifacts.ps1" `
        -Arguments @("-Date", $runDate)
}

Write-Host ""
Write-Host "[OK] Morning Ritual completed"
if (Test-Path $mainWorldSummary) {
    Write-Host ("[OK] main       : {0}" -f $mainWorldSummary)
}
if (Test-Path $predictionLatest) {
    Write-Host ("[OK] prediction : {0}" -f $predictionLatest)
}
if (Test-Path $fxDecisionLatest) {
    Write-Host ("[OK] fx decision: {0}" -f $fxDecisionLatest)
}
if (Test-Path $healthLatest) {
    Write-Host ("[OK] health     : {0}" -f $healthLatest)
}