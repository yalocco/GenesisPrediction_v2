param(
    [string]$Date = "",
    [string]$Root = "",
    [switch]$AllowDirtyRepo,
    [switch]$SkipMain,
    [switch]$SkipPredictionLayer,
    [switch]$SkipFx,
    [switch]$SkipHealth,
    [switch]$SkipRefresh,
    [switch]$DeployLabos,
    [switch]$ContinueOnError,
    [switch]$Pretty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host "[$ts] $Message"
}

function Resolve-RepoRoot {
    param([string]$ExplicitRoot)

    if (-not [string]::IsNullOrWhiteSpace($ExplicitRoot)) {
        return (Resolve-Path $ExplicitRoot).Path
    }

    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    if ($MyInvocation.MyCommand.Path) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        return (Resolve-Path (Join-Path $scriptDir "..")).Path
    }

    return (Get-Location).Path
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Log "=== $Name ==="
    try {
        & $Action
    }
    catch {
        if ($ContinueOnError) {
            Write-Warning "$Name failed: $($_.Exception.Message)"
        }
        else {
            throw
        }
    }
}

function Test-ScriptSupportsParameter {
    param(
        [string]$ScriptPath,
        [string]$ParameterName
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        return $false
    }

    try {
        $text = Get-Content -LiteralPath $ScriptPath -Raw -Encoding UTF8
        if ($text -match '(?is)param\s*\(' -and $text -match ("(?i)\[" + "switch" + "\]\s*\$" + [regex]::Escape($ParameterName) + "\b|(?i)\[" + "string" + "\]\s*\$" + [regex]::Escape($ParameterName) + "\b|(?i)\$" + [regex]::Escape($ParameterName) + "\b")) {
            return $true
        }
    }
    catch {
        return $false
    }

    return $false
}

function Test-ScriptSupportsDate {
    param([string]$ScriptPath)
    return (Test-ScriptSupportsParameter -ScriptPath $ScriptPath -ParameterName "Date")
}

function Invoke-PowerShellFile {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string]$DateValue = "",
        [switch]$PassAllowDirtyRepo,
        [switch]$PassPretty
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Log "[SKIP] missing script: $ScriptPath"
        return
    }

    $args = @(
        "-ExecutionPolicy", "Bypass",
        "-File", $ScriptPath
    )

    if (-not [string]::IsNullOrWhiteSpace($DateValue) -and (Test-ScriptSupportsDate -ScriptPath $ScriptPath)) {
        $args += @("-Date", $DateValue)
    }

    if ($PassAllowDirtyRepo -and (Test-ScriptSupportsParameter -ScriptPath $ScriptPath -ParameterName "AllowDirtyRepo")) {
        $args += "-AllowDirtyRepo"
    }

    if ($PassPretty -and (Test-ScriptSupportsParameter -ScriptPath $ScriptPath -ParameterName "Pretty")) {
        $args += "-Pretty"
    }

    Write-Host ("CMD: powershell " + ($args -join " "))
    & powershell @args
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

function Resolve-PythonCommand {
    param([string]$RepoRoot)

    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        return @{
            Executable = $venvPython
            PrefixArgs = @()
            Display    = $venvPython
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCmd) {
        return @{
            Executable = $pythonCmd.Source
            PrefixArgs = @()
            Display    = $pythonCmd.Source
        }
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyCmd) {
        return @{
            Executable = $pyCmd.Source
            PrefixArgs = @("-3")
            Display    = "$($pyCmd.Source) -3"
        }
    }

    throw "Python executable not found. Expected .venv\Scripts\python.exe, python, or py -3."
}

function Invoke-PythonFile {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Log "[SKIP] missing script: $ScriptPath"
        return
    }

    $python = Resolve-PythonCommand -RepoRoot $Root
    $cmdArgs = @()
    $cmdArgs += $python.PrefixArgs
    $cmdArgs += $ScriptPath
    if ($Arguments.Count -gt 0) {
        $cmdArgs += $Arguments
    }

    Write-Host ("CMD: " + $python.Display + " " + ($cmdArgs -join " "))
    & $python.Executable @cmdArgs
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

function Find-FirstExistingPath {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Show-GlobalStatusSummary {
    param([string]$RepoRoot)

    $globalStatusPath = Join-Path $RepoRoot "analysis\global_status_latest.json"
    if (-not (Test-Path -LiteralPath $globalStatusPath)) {
        Write-Log "[INFO] analysis\global_status_latest.json not found."
        return
    }

    try {
        $json = Get-Content -LiteralPath $globalStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host ""
        Write-Host "=== Global Status ==="
        Write-Host "AS_OF     : $($json.as_of)"
        Write-Host "RISK      : $($json.global_risk)"
        Write-Host "SENTIMENT : $($json.sentiment_balance)"
        Write-Host "FX        : $($json.fx_regime)"
        Write-Host "ARTICLES  : $($json.articles)"
        Write-Host "HEALTH    : $($json.health)"
    }
    catch {
        Write-Warning "global_status_latest.json exists but could not be parsed: $($_.Exception.Message)"
    }
}

$Root = Resolve-RepoRoot -ExplicitRoot $Root
if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Get-Date -Format "yyyy-MM-dd"
}

$scriptsDir    = Join-Path $Root "scripts"
$analysisDir   = Join-Path $Root "analysis"
$predictionDir = Join-Path $analysisDir "prediction"

$trendOutput        = Join-Path $predictionDir "trend_latest.json"
$signalOutput       = Join-Path $predictionDir "signal_latest.json"
$earlyWarningOutput = Join-Path $predictionDir "early_warning_latest.json"
$scenarioOutput     = Join-Path $predictionDir "scenario_latest.json"
$predictionOutput   = Join-Path $predictionDir "prediction_latest.json"

Write-Host "Morning Ritual (single entrypoint)"
Write-Host "ROOT        : $Root"
Write-Host "DATE        : $Date"
Write-Host ("GUARD       : " + ($(if ($AllowDirtyRepo) { "OFF" } else { "ON" })))
Write-Host ("MAIN        : " + ($(if ($SkipMain) { "SKIP" } else { "RUN" })))
Write-Host ("PREDICTION  : " + ($(if ($SkipPredictionLayer) { "SKIP" } else { "RUN" })))
Write-Host ("FX          : " + ($(if ($SkipFx) { "SKIP" } else { "RUN" })))
Write-Host ("HEALTH      : " + ($(if ($SkipHealth) { "SKIP" } else { "RUN" })))
Write-Host ("REFRESH     : " + ($(if ($SkipRefresh) { "SKIP" } else { "RUN" })))
Write-Host ("DEPLOY      : " + ($(if ($DeployLabos) { "RUN" } else { "SKIP" })))
Write-Host ("PRETTY      : " + ($(if ($Pretty) { "ON" } else { "OFF" })))
Write-Host ""

Push-Location $Root
try {
    if (-not $AllowDirtyRepo) {
        $gitStatus = git status --porcelain 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($gitStatus | Out-String))) {
            throw "Working tree is not clean. Commit/stash changes or rerun with -AllowDirtyRepo."
        }
    }
    else {
        Write-Log "Dirty repo allowed by flag."
    }

    if (-not (Test-Path -LiteralPath $predictionDir)) {
        New-Item -ItemType Directory -Force -Path $predictionDir | Out-Null
    }

    if (-not $SkipMain) {
        Invoke-Step -Name "1) run_daily_with_publish" -Action {
            Invoke-PowerShellFile `
                -Name "run_daily_with_publish" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_with_publish.ps1") `
                -DateValue $Date `
                -PassAllowDirtyRepo:$AllowDirtyRepo
        }
    }

    if (-not $SkipPredictionLayer) {
        Invoke-Step -Name "Prediction Layer 1) Trend build" -Action {
            $trendScript = Find-FirstExistingPath -Candidates @(
                (Join-Path $scriptsDir "trend_engine.py"),
                (Join-Path $scriptsDir "build_trend_latest.py")
            )

            if ($null -eq $trendScript) {
                Write-Log "[SKIP] trend build script not found."
                return
            }

            $trendArgs = @()
            if ((Split-Path -Leaf $trendScript) -ieq "trend_engine.py") {
                $trendArgs = @(
                    "--analysis-root", "analysis"
                )
            }

            Invoke-PythonFile `
                -Name "Prediction Layer 1) Trend build" `
                -ScriptPath $trendScript `
                -Arguments $trendArgs
        }

        Invoke-Step -Name "Prediction Layer 2) Signal build" -Action {
            $signalScript = Join-Path $scriptsDir "signal_engine.py"
            if (-not (Test-Path -LiteralPath $signalScript)) {
                Write-Log "[SKIP] signal_engine.py not found."
                return
            }

            Invoke-PythonFile `
                -Name "Prediction Layer 2) Signal build" `
                -ScriptPath $signalScript `
                -Arguments @(
                    "--analysis-root", "analysis",
                    "--trend-input", $trendOutput,
                    "--signal-output", $signalOutput,
                    "--early-warning-output", $earlyWarningOutput
                )
        }

        Invoke-Step -Name "Prediction Layer 3) Scenario build" -Action {
            $scenarioScript = Join-Path $scriptsDir "scenario_engine.py"
            if (-not (Test-Path -LiteralPath $scenarioScript)) {
                Write-Log "[SKIP] scenario_engine.py not found."
                return
            }

            Invoke-PythonFile `
                -Name "Prediction Layer 3) Scenario build" `
                -ScriptPath $scenarioScript `
                -Arguments @(
                    "--root", $Root,
                    "--input", $signalOutput,
                    "--early-warning-input", $earlyWarningOutput,
                    "--output-dir", $predictionDir
                )
        }

        Invoke-Step -Name "Prediction Layer 4) Prediction build" -Action {
            $predictionScript = Join-Path $scriptsDir "prediction_engine.py"
            if (-not (Test-Path -LiteralPath $predictionScript)) {
                Write-Log "[SKIP] prediction_engine.py not found."
                return
            }

            Invoke-PythonFile `
                -Name "Prediction Layer 4) Prediction build" `
                -ScriptPath $predictionScript `
                -Arguments @(
                    "--root", $Root,
                    "--input", $scenarioOutput,
                    "--output-dir", $predictionDir
                )
        }
    }

    if (-not $SkipFx) {
        Invoke-Step -Name "FX Lane 1) Daily rates" -Action {
            Invoke-PowerShellFile `
                -Name "FX Lane 1) Daily rates" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_fx_rates.ps1") `
                -DateValue $Date
        }

        Invoke-Step -Name "FX Lane 2) Daily inputs" -Action {
            Invoke-PowerShellFile `
                -Name "FX Lane 2) Daily inputs" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_fx_inputs.ps1") `
                -DateValue $Date
        }

        Invoke-Step -Name "FX Lane 3) Daily overlay" -Action {
            Invoke-PowerShellFile `
                -Name "FX Lane 3) Daily overlay" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_fx_overlay.ps1") `
                -DateValue $Date
        }
    }

    if (-not $SkipHealth) {
        Invoke-Step -Name "Health lane" -Action {
            Invoke-PowerShellFile `
                -Name "Health lane" `
                -ScriptPath (Join-Path $scriptsDir "run_health_checks.ps1") `
                -DateValue $Date
        }
    }

    if (-not $SkipRefresh) {
        Invoke-Step -Name "Refresh latest artifacts" -Action {
            $refreshCandidates = @(
                (Join-Path $scriptsDir "refresh_latest_artifacts.ps1"),
                (Join-Path $scriptsDir "refresh_latest.ps1"),
                (Join-Path $scriptsDir "materialize_latest.ps1")
            )

            $refreshScript = $refreshCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
            if ($null -eq $refreshScript -or [string]::IsNullOrWhiteSpace($refreshScript)) {
                Write-Log "[SKIP] refresh script not found."
                return
            }

            Invoke-PowerShellFile `
                -Name "Refresh latest artifacts" `
                -ScriptPath $refreshScript `
                -DateValue $Date `
                -PassPretty:$Pretty
        }
    }

    Invoke-Step -Name "Global Status build" -Action {
        Invoke-PythonFile `
            -Name "Global Status build" `
            -ScriptPath (Join-Path $scriptsDir "build_global_status_latest.py") `
            -Arguments @(
                "--root", $Root,
                "--pretty"
            )
    }

    Show-GlobalStatusSummary -RepoRoot $Root

    if ($DeployLabos) {
        Invoke-Step -Name "LABOS Deploy 1) Build payload" -Action {
            Invoke-PowerShellFile `
                -Name "LABOS Deploy 1) Build payload" `
                -ScriptPath (Join-Path $scriptsDir "build_labos_deploy_payload.ps1")
        }

        Invoke-Step -Name "LABOS Deploy 2) Upload" -Action {
            Invoke-PowerShellFile `
                -Name "LABOS Deploy 2) Upload" `
                -ScriptPath (Join-Path $scriptsDir "run_deploy_labos.ps1")
        }
    }
    else {
        Write-Log "LABOS deploy skipped. Use -DeployLabos on home PC only."
    }

    Write-Log "Morning Ritual completed successfully."
    exit 0
}
catch {
    Write-Host "Morning Ritual finished with warnings/errors."
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}