[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$Date = "",
    [switch]$Pretty
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param(
        [string]$ExplicitRoot
    )

    if ($ExplicitRoot -and $ExplicitRoot.Trim() -ne "") {
        return (Resolve-Path $ExplicitRoot).Path
    }

    if ($PSScriptRoot) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    return (Get-Location).Path
}

function Resolve-RunDate {
    param(
        [string]$ExplicitDate
    )

    if ($ExplicitDate -and $ExplicitDate.Trim() -ne "") {
        return $ExplicitDate.Trim()
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
            try {
                $null = Get-Command python -ErrorAction Stop
                return "python"
            }
            catch {
                continue
            }
        }

        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Python executable not found."
}

function Ensure-AnalysisDir {
    param(
        [string]$RepoRoot
    )

    $analysisDir = Join-Path $RepoRoot "analysis"

    if (-not (Test-Path $analysisDir)) {
        New-Item -ItemType Directory -Path $analysisDir -Force | Out-Null
    }
}

function Copy-IfExists {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    if (-not (Test-Path $SourcePath)) {
        return $false
    }

    $destDir = Split-Path -Parent $DestinationPath

    if ($destDir -and -not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    Copy-Item -Path $SourcePath -Destination $DestinationPath -Force

    Write-Host "[copy] $SourcePath -> $DestinationPath" -ForegroundColor Green

    return $true
}

function Refresh-KnownLatestArtifacts {
    param(
        [string]$RepoRoot
    )

    $copyRules = @(

        # daily summary
        @{
            Source = (Join-Path $RepoRoot "data\world_politics\analysis\daily_summary_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\daily_summary_latest.json")
        },

        # sentiment
        @{
            Source = (Join-Path $RepoRoot "data\world_politics\analysis\sentiment_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\sentiment_latest.json")
        },

        # health
        @{
            Source = (Join-Path $RepoRoot "data\world_politics\analysis\health_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\health_latest.json")
        },

        # prediction
        @{
            Source = (Join-Path $RepoRoot "analysis\prediction\prediction_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\prediction_latest.json")
        },

        # scenario
        @{
            Source = (Join-Path $RepoRoot "analysis\prediction\scenario_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\scenario_latest.json")
        },

        # signal
        @{
            Source = (Join-Path $RepoRoot "analysis\prediction\signal_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\signal_latest.json")
        }
    )

    foreach ($rule in $copyRules) {
        Copy-IfExists `
            -SourcePath $rule.Source `
            -DestinationPath $rule.Destination | Out-Null
    }
}

function Build-GlobalStatusLatest {
    param(
        [string]$RepoRoot,
        [switch]$PrettyJson
    )

    $runner = Join-Path $RepoRoot "scripts\run_global_status_latest.ps1"

    $args = @(
        "-Root", $RepoRoot
    )

    if ($PrettyJson) {
        $args += "-Pretty"
    }

    powershell -ExecutionPolicy Bypass -File $runner @args
}

function Show-Summary {
    param(
        [string]$RepoRoot
    )

    $globalStatusPath = Join-Path $RepoRoot "analysis\global_status_latest.json"

    Write-Host ""
    Write-Host "=== refresh_latest_artifacts summary ===" -ForegroundColor Cyan

    if (Test-Path $globalStatusPath) {

        $json = Get-Content $globalStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json

        Write-Host "global_status_latest.json : OK"
        Write-Host "  as_of      : $($json.as_of)"
        Write-Host "  risk       : $($json.global_risk)"
        Write-Host "  sentiment  : $($json.sentiment_balance)"
        Write-Host "  fx         : $($json.fx_regime)"
        Write-Host "  articles   : $($json.articles)"
        Write-Host "  health     : $($json.health)"
    }
}

try {

    $repoRoot = Resolve-RepoRoot -ExplicitRoot $Root
    $runDate = Resolve-RunDate -ExplicitDate $Date
    $pythonCmd = Resolve-PythonCommand -RepoRoot $repoRoot

    Write-Host "GenesisPrediction - refresh_latest_artifacts" -ForegroundColor Cyan
    Write-Host "ROOT   : $repoRoot"
    Write-Host "DATE   : $runDate"
    Write-Host "PYTHON : $pythonCmd"
    Write-Host ""

    Ensure-AnalysisDir -RepoRoot $repoRoot

    Write-Host "[1/2] refresh known latest artifacts" -ForegroundColor Cyan
    Refresh-KnownLatestArtifacts -RepoRoot $repoRoot

    Write-Host ""
    Write-Host "[2/2] build analysis/global_status_latest.json" -ForegroundColor Cyan
    Build-GlobalStatusLatest -RepoRoot $repoRoot -PrettyJson:$Pretty

    Show-Summary -RepoRoot $repoRoot

    exit 0
}
catch {
    Write-Error $_
    exit 1
}