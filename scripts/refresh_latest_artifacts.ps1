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

function Ensure-Directory {
    param(
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Copy-IfExists {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    if (-not (Test-Path $SourcePath)) {
        Write-Host "[skip] missing: $SourcePath" -ForegroundColor DarkYellow
        return $false
    }

    $destDir = Split-Path -Parent $DestinationPath
    if ($destDir) {
        Ensure-Directory -Path $destDir
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

        # world / digest-related aliases into analysis/
        @{
            Source      = (Join-Path $RepoRoot "data\world_politics\analysis\daily_summary_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\daily_summary_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "data\world_politics\analysis\sentiment_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\sentiment_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "data\world_politics\analysis\health_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\health_latest.json")
        },

        # prediction layer aliases into analysis/
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\trend_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\trend_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\signal_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\signal_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\early_warning_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\early_warning_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\scenario_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\scenario_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\prediction_latest.json")
            Destination = (Join-Path $RepoRoot "analysis\prediction_latest.json")
        }
    )

    $copied = 0

    foreach ($rule in $copyRules) {
        if (Copy-IfExists -SourcePath $rule.Source -DestinationPath $rule.Destination) {
            $copied++
        }
    }

    return $copied
}

function Save-PredictionHistorySnapshot {
    param(
        [string]$RepoRoot,
        [string]$RunDate
    )

    $sourcePath = Join-Path $RepoRoot "analysis\prediction\prediction_latest.json"
    $historyDir = Join-Path $RepoRoot ("analysis\prediction\history\{0}" -f $RunDate)
    $destPath   = Join-Path $historyDir "prediction.json"

    Ensure-Directory -Path $historyDir

    if (Copy-IfExists -SourcePath $sourcePath -DestinationPath $destPath) {
        return $destPath
    }

    return $null
}

function Publish-PredictionArtifacts {
    param(
        [string]$RepoRoot
    )

    $publishDir = Join-Path $RepoRoot "data\prediction"
    Ensure-Directory -Path $publishDir

    $publishRules = @(
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\trend_latest.json")
            Destination = (Join-Path $publishDir "trend_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\signal_latest.json")
            Destination = (Join-Path $publishDir "signal_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\early_warning_latest.json")
            Destination = (Join-Path $publishDir "early_warning_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\scenario_latest.json")
            Destination = (Join-Path $publishDir "scenario_latest.json")
        },
        @{
            Source      = (Join-Path $RepoRoot "analysis\prediction\prediction_latest.json")
            Destination = (Join-Path $publishDir "prediction_latest.json")
        }
    )

    $published = 0

    foreach ($rule in $publishRules) {
        if (Copy-IfExists -SourcePath $rule.Source -DestinationPath $rule.Destination) {
            $published++
        }
    }

    return $published
}

function Build-GlobalStatusLatest {
    param(
        [string]$RepoRoot,
        [switch]$PrettyJson
    )

    $runner = Join-Path $RepoRoot "scripts\run_global_status_latest.ps1"

    if (-not (Test-Path $runner)) {
        throw "Global status runner not found: $runner"
    }

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
        [string]$RepoRoot,
        [string]$RunDate,
        [int]$LatestCopied,
        [int]$PublishedCount,
        [string]$PredictionHistoryPath
    )

    $globalStatusPath = Join-Path $RepoRoot "analysis\global_status_latest.json"

    Write-Host ""
    Write-Host "=== refresh_latest_artifacts summary ===" -ForegroundColor Cyan
    Write-Host "date                    : $RunDate"
    Write-Host "latest aliases copied   : $LatestCopied"
    Write-Host "prediction published    : $PublishedCount"

    if ($PredictionHistoryPath) {
        Write-Host "prediction history      : $PredictionHistoryPath"
    }
    else {
        Write-Host "prediction history      : not updated"
    }

    if (Test-Path $globalStatusPath) {
        $json = Get-Content $globalStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json

        Write-Host "global_status_latest    : OK"
        Write-Host "  as_of      : $($json.as_of)"
        Write-Host "  risk       : $($json.global_risk)"
        Write-Host "  sentiment  : $($json.sentiment_balance)"
        Write-Host "  fx         : $($json.fx_regime)"
        Write-Host "  articles   : $($json.articles)"
        Write-Host "  health     : $($json.health)"
    }
    else {
        Write-Host "global_status_latest    : missing" -ForegroundColor DarkYellow
    }
}

try {
    $repoRoot = Resolve-RepoRoot -ExplicitRoot $Root
    $runDate  = Resolve-RunDate -ExplicitDate $Date

    Write-Host "GenesisPrediction - refresh_latest_artifacts" -ForegroundColor Cyan
    Write-Host "ROOT : $repoRoot"
    Write-Host "DATE : $runDate"
    Write-Host ""

    Ensure-Directory -Path (Join-Path $repoRoot "analysis")
    Ensure-Directory -Path (Join-Path $repoRoot "analysis\prediction")
    Ensure-Directory -Path (Join-Path $repoRoot "analysis\prediction\history")
    Ensure-Directory -Path (Join-Path $repoRoot "data\prediction")

    Write-Host "[1/4] refresh known latest artifacts" -ForegroundColor Cyan
    $latestCopied = Refresh-KnownLatestArtifacts -RepoRoot $repoRoot

    Write-Host ""
    Write-Host "[2/4] save prediction history snapshot" -ForegroundColor Cyan
    $predictionHistoryPath = Save-PredictionHistorySnapshot -RepoRoot $repoRoot -RunDate $runDate

    Write-Host ""
    Write-Host "[3/4] publish prediction artifacts" -ForegroundColor Cyan
    $publishedCount = Publish-PredictionArtifacts -RepoRoot $repoRoot

    Write-Host ""
    Write-Host "[4/4] build analysis/global_status_latest.json" -ForegroundColor Cyan
    Build-GlobalStatusLatest -RepoRoot $repoRoot -PrettyJson:$Pretty

    Show-Summary `
        -RepoRoot $repoRoot `
        -RunDate $runDate `
        -LatestCopied $latestCopied `
        -PublishedCount $publishedCount `
        -PredictionHistoryPath $predictionHistoryPath

    exit 0
}
catch {
    Write-Error $_
    exit 1
}