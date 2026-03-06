param(
    [string]$Date = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$targetPy  = Join-Path $repoRoot "scripts\save_observation_memory.py"

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: python not found: $pythonExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $targetPy)) {
    Write-Host "ERROR: target script not found: $targetPy" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Get-Date -Format "yyyy-MM-dd"
}

Write-Host ""
Write-Host "=== save_observation_memory ===" -ForegroundColor Cyan
Write-Host "ROOT : $repoRoot"
Write-Host "DATE : $Date"
Write-Host "CMD  : $pythonExe $targetPy --date $Date"
Write-Host ""

& $pythonExe $targetPy --date $Date

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "save_observation_memory failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "save_observation_memory completed." -ForegroundColor Green
exit 0