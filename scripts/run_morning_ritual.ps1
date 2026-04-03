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
    param([string]$InputDate)

    if (-not [string]::IsNullOrWhiteSpace($InputDate)) {
        return $InputDate
    }
    return (Get-Date).ToString("yyyy-MM-dd")
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
        [string]$Name,
        [string]$RepoRoot,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    Write-Host ""
    Write-Host ("[{0}] === {1} ===" -f (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss"), $Name)

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
    param([string]$Path, [string]$Message = "")

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

$mainWorldSummary = Join-Path $repoRoot "analysis\daily_summary_latest.json"
$predictionLatest = Join-Path $repoRoot "analysis\prediction\prediction_latest.json"
$fxDecisionLatest = Join-Path $repoRoot "analysis\fx\fx_decision_latest.json"
$healthLatest = Join-Path $repoRoot "analysis\health_latest.json"
$sentimentLatest = Join-Path $repoRoot "data\world_politics\analysis\sentiment_latest.json"
$predictionHistoryIndex = Join-Path $repoRoot "data\prediction\prediction_history_index.json"
$globalStatusLatest = Join-Path $repoRoot "analysis\global_status_latest.json"

# ============================================================
# 1) Main lane
# ============================================================
if (-not $SkipMain) {
    Invoke-PowerShellScript -Name "run_daily_with_publish" -RepoRoot $repoRoot -ScriptPath "scripts/run_daily_with_publish.ps1" -Arguments @("-Date", $runDate)
    Invoke-PythonScript -Name "build_daily_sentiment" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/build_daily_sentiment.py" -Arguments @("--date", $runDate)

    if ($Guard) {
        Assert-PathExists -Path $mainWorldSummary
        Assert-PathExists -Path $sentimentLatest
    }
}

# ============================================================
# 2) Prediction lane
# ============================================================
if (-not $SkipPrediction) {

    Invoke-PythonScript -Name "trend_engine" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/trend_engine.py"
    Invoke-PythonScript -Name "signal_engine" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/signal_engine.py"
    Invoke-PythonScript -Name "scenario_engine" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/scenario_engine.py"
    Invoke-PythonScript -Name "prediction_engine" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/prediction_engine.py"
    Invoke-PythonScript -Name "build_prediction_history_index" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/build_prediction_history_index.py"

    # ============================
    # Explanation Layer（非ブロッキング）
    # ============================
    try {
        Invoke-PythonScript -Name "prediction_explanation" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/build_prediction_explanation.py"
        Invoke-PythonScript -Name "scenario_explanation" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/build_scenario_explanation.py"
    }
    catch {
        Write-Warning "Explanation Layer failed (non-blocking)"
    }

    if ($Guard) {
        Assert-PathExists -Path $predictionLatest
        Assert-PathExists -Path $predictionHistoryIndex
    }
}

# ============================================================
# 3) FX lane
# ============================================================
if (-not $SkipFx) {
    Invoke-PowerShellScript -Name "run_daily_fx_rates" -RepoRoot $repoRoot -ScriptPath "scripts/run_daily_fx_rates.ps1"
    Invoke-PowerShellScript -Name "run_daily_fx_inputs" -RepoRoot $repoRoot -ScriptPath "scripts/run_daily_fx_inputs.ps1"
    Invoke-PowerShellScript -Name "run_daily_fx_overlay" -RepoRoot $repoRoot -ScriptPath "scripts/run_daily_fx_overlay.ps1"
    Invoke-PowerShellScript -Name "run_daily_fx_decision" -RepoRoot $repoRoot -ScriptPath "scripts/run_daily_fx_decision.ps1" -Arguments @("-Date", $runDate, "-Strict")

    if ($Guard) {
        Assert-PathExists -Path $fxDecisionLatest
    }
}

# ============================================================
# 4) Health lane
# ============================================================
if (-not $SkipHealth) {
    Invoke-PythonScript -Name "build_data_health" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/build_data_health.py"

    if ($Guard) {
        Assert-PathExists -Path $healthLatest
    }
}

# ============================================================
# 5) Refresh lane
# ============================================================
if (-not $SkipRefresh) {
    Invoke-PowerShellScript -Name "refresh_latest_artifacts" -RepoRoot $repoRoot -ScriptPath "scripts/refresh_latest_artifacts.ps1" -Arguments @("-Date", $runDate)
}

# ============================================================
# 6) Global Status lane
# ============================================================
Invoke-PythonScript -Name "build_global_status" -RepoRoot $repoRoot -PythonExe $pythonExe -ScriptPath "scripts/build_global_status.py"

if ($Guard) {
    Assert-PathExists -Path $globalStatusLatest
}

Write-Host ""
Write-Host "[OK] Morning Ritual completed"
