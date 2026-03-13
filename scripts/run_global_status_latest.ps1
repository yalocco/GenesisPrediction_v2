[CmdletBinding()]
param(
    [string]$Root = "",
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

    throw "Python executable not found. Checked .venv, venv, and PATH."
}

function Invoke-GlobalStatusBuild {
    param(
        [string]$RepoRoot,
        [switch]$PrettyJson
    )

    $pythonCmd = Resolve-PythonCommand -RepoRoot $RepoRoot
    $scriptPath = Join-Path $RepoRoot "scripts\build_global_status_latest.py"

    if (-not (Test-Path $scriptPath)) {
        throw "Missing script: $scriptPath"
    }

    $args = @(
        $scriptPath,
        "--root",
        $RepoRoot
    )

    if ($PrettyJson) {
        $args += "--pretty"
    }

    Write-Host "GenesisPrediction - run_global_status_latest" -ForegroundColor Cyan
    Write-Host "ROOT   : $RepoRoot"
    Write-Host "PYTHON : $pythonCmd"
    Write-Host "SCRIPT : $scriptPath"
    Write-Host "PRETTY : $($PrettyJson.IsPresent)"

    & $pythonCmd @args
    if ($LASTEXITCODE -ne 0) {
        throw "build_global_status_latest.py failed with exit code $LASTEXITCODE"
    }
}

function Show-OutputSummary {
    param(
        [string]$RepoRoot
    )

    $outPath = Join-Path $RepoRoot "analysis\global_status_latest.json"
    if (-not (Test-Path $outPath)) {
        throw "Output not found: $outPath"
    }

    $json = Get-Content $outPath -Raw -Encoding UTF8 | ConvertFrom-Json

    Write-Host ""
    Write-Host "[ok] global_status_latest.json updated" -ForegroundColor Green
    Write-Host "PATH      : $outPath"
    Write-Host "AS_OF     : $($json.as_of)"
    Write-Host "RISK      : $($json.global_risk)"
    Write-Host "SENTIMENT : $($json.sentiment_balance)"
    Write-Host "FX        : $($json.fx_regime)"
    Write-Host "ARTICLES  : $($json.articles)"
    Write-Host "HEALTH    : $($json.health)"
}

try {
    $repoRoot = Resolve-RepoRoot -ExplicitRoot $Root

    Invoke-GlobalStatusBuild -RepoRoot $repoRoot -PrettyJson:$Pretty
    Show-OutputSummary -RepoRoot $repoRoot

    exit 0
}
catch {
    Write-Error $_
    exit 1
}