[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Date = (Get-Date).ToString('yyyy-MM-dd'),
    [switch]$AllowDirtyRepo,
    [switch]$ContinueOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section([string]$Message) {
    $ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
    Write-Host "[$ts] === $Message ==="
}

function Test-CommandExists([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PythonExe([string]$RootPath) {
    $candidates = @(
        (Join-Path $RootPath '.venv\Scripts\python.exe'),
        (Join-Path $RootPath 'venv\Scripts\python.exe'),
        'python'
    )
    foreach ($candidate in $candidates) {
        if ($candidate -eq 'python') {
            if (Test-CommandExists 'python') { return 'python' }
        } elseif (Test-Path $candidate) {
            return $candidate
        }
    }
    throw 'python executable not found.'
}

function Invoke-Step {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$Optional
    )

    if (-not (Test-Path $FilePath)) {
        if ($Optional) {
            Write-Host "[SKIP] $Name (missing: $FilePath)"
            return
        }
        throw "$Name script not found: $FilePath"
    }

    $cmdText = @($script:PythonExe, $FilePath) + $Arguments
    Write-Host ('CMD: ' + ($cmdText -join ' '))
    & $script:PythonExe $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        if ($Optional -and $ContinueOnError) {
            Write-Warning "$Name failed with exit code $exitCode. Continuing."
            return
        }
        throw "$Name failed with exit code $exitCode."
    }
}

function Invoke-PowerShellFile {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$Optional
    )

    if (-not (Test-Path $FilePath)) {
        if ($Optional) {
            Write-Host "[SKIP] $Name (missing: $FilePath)"
            return
        }
        throw "$Name script not found: $FilePath"
    }

    $cmdText = @('powershell', '-ExecutionPolicy', 'Bypass', '-File', $FilePath) + $Arguments
    Write-Host ('CMD: ' + ($cmdText -join ' '))
    & powershell -ExecutionPolicy Bypass -File $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        if ($Optional -and $ContinueOnError) {
            Write-Warning "$Name failed with exit code $exitCode. Continuing."
            return
        }
        throw "$Name failed with exit code $exitCode."
    }
}

function Ensure-Parent([string]$Path) {
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
}

function Copy-IfExists([string]$Source, [string]$Destination) {
    if (Test-Path $Source) {
        Ensure-Parent $Destination
        Copy-Item -Path $Source -Destination $Destination -Force
        Write-Host "[OK] alias: $Destination <= $Source"
        return $true
    }
    return $false
}

function Ensure-AnalysisAliases([string]$RootPath, [string]$AsOfDate) {
    $analysisDir = Join-Path $RootPath 'data\world_politics\analysis'
    if (-not (Test-Path $analysisDir)) {
        Write-Warning "analysis directory not found: $analysisDir"
        return
    }

    $latestCandidates = @(
        (Join-Path $analysisDir 'daily_news_latest.json'),
        (Join-Path $analysisDir 'latest.json')
    )
    $summaryCandidates = @(
        (Join-Path $analysisDir 'daily_summary_latest.json'),
        (Join-Path $analysisDir 'summary.json')
    )

    $newsSource = $latestCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    $summarySource = $summaryCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($newsSource) {
        Copy-IfExists $newsSource (Join-Path $analysisDir 'daily_news_latest.json') | Out-Null
        Copy-IfExists $newsSource (Join-Path $analysisDir ("daily_news_{0}.json" -f $AsOfDate)) | Out-Null
    }
    if ($summarySource) {
        Copy-IfExists $summarySource (Join-Path $analysisDir 'daily_summary_latest.json') | Out-Null
        Copy-IfExists $summarySource (Join-Path $analysisDir ("daily_summary_{0}.json" -f $AsOfDate)) | Out-Null
    }
}

function Publish-PredictionSnapshot([string]$RootPath, [string]$AsOfDate) {
    $predictionDir = Join-Path $RootPath 'analysis\prediction'
    if (-not (Test-Path $predictionDir)) {
        Write-Host "[SKIP] publish prediction snapshot (missing: $predictionDir)"
        return
    }

    $historyDir = Join-Path $RootPath ("analysis\prediction_history\{0}" -f $AsOfDate)
    New-Item -ItemType Directory -Path $historyDir -Force | Out-Null

    $pairs = @(
        @{ Source = 'trend_latest.json'; Target = 'trend.json' },
        @{ Source = 'signal_latest.json'; Target = 'signal.json' },
        @{ Source = 'early_warning_latest.json'; Target = 'early_warning.json' },
        @{ Source = 'scenario_latest.json'; Target = 'scenario.json' },
        @{ Source = 'prediction_latest.json'; Target = 'prediction.json' }
    )

    foreach ($pair in $pairs) {
        $src = Join-Path $predictionDir $pair.Source
        $dst = Join-Path $historyDir $pair.Target
        if (Test-Path $src) {
            Copy-Item -Path $src -Destination $dst -Force
            Write-Host "[OK] publish: $dst"
        }
    }
}

try {
    $Root = (Resolve-Path $Root).Path
    Set-Location $Root
    $script:PythonExe = Get-PythonExe $Root

    Write-Host 'GenesisPrediction v2 - run_daily_with_publish'
    Write-Host "ROOT : $Root"
    Write-Host "DATE : $Date"
    Write-Host ("GUARD: {0}" -f ($(if ($AllowDirtyRepo) { 'OFF' } else { 'ON' })))
    Write-Host ''

    if (-not $AllowDirtyRepo -and (Test-Path (Join-Path $Root '.git'))) {
        $statusLines = git status --porcelain
        if ($LASTEXITCODE -eq 0 -and $statusLines) {
            throw 'Working tree is not clean. Commit/stash changes or rerun with -AllowDirtyRepo.'
        }
    }

    Write-Section '1) Analyzer (docker compose run --rm analyzer)'
    if (Test-Path (Join-Path $Root 'docker-compose.yml') -or Test-Path (Join-Path $Root 'compose.yml')) {
        if (-not (Test-CommandExists 'docker')) {
            throw 'docker command not found.'
        }
        Write-Host 'CMD: docker compose run --rm analyzer'
        & docker compose run --rm analyzer
        if ($LASTEXITCODE -ne 0) {
            throw '1) Analyzer failed.'
        }
    } else {
        Write-Host '[SKIP] docker compose file not found'
    }

    Write-Section '1.5) Normalize analysis aliases'
    Ensure-AnalysisAliases -RootPath $Root -AsOfDate $Date

    Write-Section '2) Build daily sentiment'
    Invoke-Step -Name '2) Build daily sentiment' -FilePath (Join-Path $Root 'scripts\build_daily_sentiment.py') -Arguments @('--date', $Date)

    Write-Section '3) Build digest view model'
    Invoke-Step -Name '3) Build digest view model' -FilePath (Join-Path $Root 'scripts\build_digest_view_model.py') -Arguments @('--date', $Date) -Optional

    Write-Section '4) Trend engine'
    Invoke-Step -Name '4) Trend engine' -FilePath (Join-Path $Root 'scripts\trend_engine.py') -Arguments @('--date', $Date) -Optional

    Write-Section '5) Signal engine'
    Invoke-Step -Name '5) Signal engine' -FilePath (Join-Path $Root 'scripts\signal_engine.py') -Arguments @('--date', $Date) -Optional

    Write-Section '6) Scenario engine'
    Invoke-Step -Name '6) Scenario engine' -FilePath (Join-Path $Root 'scripts\scenario_engine.py') -Arguments @('--date', $Date) -Optional

    Write-Section '7) Prediction engine'
    Invoke-Step -Name '7) Prediction engine' -FilePath (Join-Path $Root 'scripts\prediction_engine.py') -Arguments @('--date', $Date) -Optional

    Write-Section '8) Publish prediction history snapshot'
    Publish-PredictionSnapshot -RootPath $Root -AsOfDate $Date

    Write-Host 'run_daily_with_publish completed successfully.'
    exit 0
}
catch {
    Write-Host 'run_daily_with_publish finished with warnings/errors.' -ForegroundColor Yellow
    Write-Error $_
    exit 1
}
