[CmdletBinding()]
param(
    [string]$Date = "",
    [switch]$Guard,
    [switch]$SkipAnalyze,
    [switch]$SkipPrediction,
    [switch]$SkipPublish,
    [switch]$ContinueOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    Write-Host "[$ts] $Message"
}

function Fail-Or-Continue {
    param([string]$Message)
    if ($ContinueOnError) {
        Write-Warning $Message
    }
    else {
        throw $Message
    }
}

function Resolve-Python {
    $candidates = @(
        (Join-Path $Root ".venv/Scripts/python.exe"),
        (Join-Path $Root ".venv/bin/python"),
        "python",
        "py"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python" -or $candidate -eq "py") {
            $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($null -ne $cmd) {
                return $candidate
            }
        }
        elseif (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Python runtime was not found. Expected .venv or PATH python."
}

function Resolve-DockerComposeCommand {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $docker) {
        return $null
    }

    $composeCheck = & docker compose version 2>$null
    if ($LASTEXITCODE -eq 0) {
        return @("docker", "compose")
    }

    $dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
    if ($null -ne $dockerCompose) {
        return @("docker-compose")
    }

    return $null
}

function Invoke-External {
    param(
        [string]$Title,
        [string[]]$Command,
        [string]$WorkingDirectory = $Root,
        [switch]$Optional
    )

    Write-Log "=== $Title ==="
    Write-Host ("CMD: " + ($Command -join " "))

    Push-Location $WorkingDirectory
    try {
        & $Command[0] @($Command[1..($Command.Length - 1)])
        if ($LASTEXITCODE -ne 0) {
            $message = "$Title failed with exit code $LASTEXITCODE."
            if ($Optional) {
                Fail-Or-Continue $message
            }
            else {
                throw $message
            }
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-PythonScript {
    param(
        [string]$Title,
        [string]$ScriptPath,
        [string[]]$Arguments = @(),
        [switch]$Optional
    )

    if (-not (Test-Path $ScriptPath)) {
        $message = "$Title skipped: script not found -> $ScriptPath"
        if ($Optional) {
            Write-Log $message
            return
        }
        throw $message
    }

    $python = Resolve-Python
    $cmd = @($python, $ScriptPath) + $Arguments
    Invoke-External -Title $Title -Command $cmd -Optional:$Optional
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Copy-IfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path $Source) {
        Copy-Item -Path $Source -Destination $Destination -Force
        return $true
    }

    return $false
}

function Get-DefaultDate {
    return ([DateTime]::UtcNow.ToString("yyyy-MM-dd"))
}

if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Get-DefaultDate
}

$PredictionDir = Join-Path $Root "analysis/prediction"
$PredictionHistoryDir = Join-Path $Root "analysis/prediction_history/$Date"
Ensure-Directory -Path $PredictionDir
Ensure-Directory -Path $PredictionHistoryDir

Write-Host ""
Write-Host "GenesisPrediction v2 - run_daily_with_publish"
Write-Host "ROOT : $Root"
Write-Host "DATE : $Date"
Write-Host "GUARD: $([string]::new($(if ($Guard) { 'ON' } else { 'OFF' })))"
Write-Host ""

$pipelineFailed = $false

try {
    if (-not $SkipAnalyze) {
        $compose = Resolve-DockerComposeCommand
        if ($null -ne $compose) {
            $analyzerCmd = $compose + @("run", "--rm", "analyzer")
            Invoke-External -Title "1) Analyzer (docker compose run --rm analyzer)" -Command $analyzerCmd
        }
        else {
            Write-Log "Analyzer step skipped: docker compose command not found."
        }

        $optionalPythonSteps = @(
            @{ Title = "2) Build daily sentiment"; Script = (Join-Path $Root "scripts/build_daily_sentiment.py"); Args = @() },
            @{ Title = "3) Build digest view model"; Script = (Join-Path $Root "scripts/build_digest_view_model.py"); Args = @() },
            @{ Title = "4) Refresh latest artifacts"; Script = (Join-Path $Root "scripts/refresh_latest_artifacts.py"); Args = @() }
        )

        foreach ($step in $optionalPythonSteps) {
            Invoke-PythonScript -Title $step.Title -ScriptPath $step.Script -Arguments $step.Args -Optional
        }
    }

    if (-not $SkipPrediction) {
        $trendScript = Join-Path $Root "scripts/trend_engine.py"
        $signalScript = Join-Path $Root "scripts/signal_engine.py"
        $scenarioScript = Join-Path $Root "scripts/scenario_engine.py"
        $predictionScript = Join-Path $Root "scripts/prediction_engine.py"

        Invoke-PythonScript -Title "5) Trend Engine" -ScriptPath $trendScript -Arguments @("--date", $Date) -Optional
        Invoke-PythonScript -Title "6) Signal Engine" -ScriptPath $signalScript -Arguments @("--date", $Date)
        Invoke-PythonScript -Title "7) Scenario Engine" -ScriptPath $scenarioScript -Arguments @("--date", $Date)
        Invoke-PythonScript -Title "8) Prediction Engine" -ScriptPath $predictionScript -Arguments @("--date", $Date)
    }

    if (-not $SkipPublish) {
        Write-Log "=== 9) Publish prediction artifacts ==="

        $published = @()
        $filesToPublish = @(
            @{ Name = "trend_latest.json"; Source = (Join-Path $PredictionDir "trend_latest.json"); Destination = (Join-Path $PredictionHistoryDir "trend.json") },
            @{ Name = "signal_latest.json"; Source = (Join-Path $PredictionDir "signal_latest.json"); Destination = (Join-Path $PredictionHistoryDir "signal.json") },
            @{ Name = "early_warning_latest.json"; Source = (Join-Path $PredictionDir "early_warning_latest.json"); Destination = (Join-Path $PredictionHistoryDir "early_warning.json") },
            @{ Name = "scenario_latest.json"; Source = (Join-Path $PredictionDir "scenario_latest.json"); Destination = (Join-Path $PredictionHistoryDir "scenario.json") },
            @{ Name = "prediction_latest.json"; Source = (Join-Path $PredictionDir "prediction_latest.json"); Destination = (Join-Path $PredictionHistoryDir "prediction.json") }
        )

        foreach ($item in $filesToPublish) {
            if (Copy-IfExists -Source $item.Source -Destination $item.Destination) {
                $published += $item.Name
                Write-Log ("Published: " + $item.Name)
            }
            else {
                Write-Log ("Missing (skip publish): " + $item.Name)
            }
        }

        $manifest = [ordered]@{
            date = $Date
            published_at = (Get-Date).ToUniversalTime().ToString("o")
            root = $Root
            prediction_dir = $PredictionDir
            history_dir = $PredictionHistoryDir
            published_files = $published
            prediction_available = (Test-Path (Join-Path $PredictionDir "prediction_latest.json"))
        }

        $manifestPath = Join-Path $PredictionHistoryDir "manifest.json"
        $manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $manifestPath -Encoding UTF8
        Write-Log "Manifest written: $manifestPath"
    }

    Write-Host ""
    Write-Host "run_daily_with_publish completed."
    Write-Host ""
}
catch {
    $pipelineFailed = $true
    Write-Error $_
    if (-not $ContinueOnError) {
        exit 1
    }
}
finally {
    if ($pipelineFailed) {
        Write-Host "run_daily_with_publish finished with warnings/errors."
    }
}
