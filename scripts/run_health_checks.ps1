Param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "[Health] Data Health Checks"
Write-Host "ROOT : $Root"
Write-Host "DATE : $Date"

$AnalysisDir = Join-Path $Root "data/world_politics/analysis"
$Script = Join-Path $Root "scripts/build_data_health.py"

if (!(Test-Path $Script)) {
    Write-Error "Missing script: $Script"
    exit 1
}

$python = Join-Path $Root ".venv/Scripts/python.exe"

if (!(Test-Path $python)) {
    $python = "python"
}

Write-Host "PYTHON : $python"
Write-Host "SCRIPT : $Script"
Write-Host "ANALYSIS: $AnalysisDir"

& $python $Script `
    --analysis-dir $AnalysisDir `
    --date $Date `
    --write-dated

if ($LASTEXITCODE -ne 0) {
    Write-Error "Health check failed"
    exit $LASTEXITCODE
}

Write-Host "[Health] Completed"