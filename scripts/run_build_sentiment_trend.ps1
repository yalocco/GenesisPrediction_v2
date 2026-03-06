param(
    [string]$AsOf = "",
    [int]$Window = 7
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$targetPy  = Join-Path $repoRoot "scripts\build_sentiment_trend.py"

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: python not found: $pythonExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $targetPy)) {
    Write-Host "ERROR: target script not found: $targetPy" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== build_sentiment_trend ===" -ForegroundColor Cyan
Write-Host "ROOT   : $repoRoot"
Write-Host "WINDOW : $Window"

if ([string]::IsNullOrWhiteSpace($AsOf)) {
    Write-Host "AS_OF  : latest available"
    Write-Host "CMD    : $pythonExe $targetPy --window $Window --verbose"
    Write-Host ""
    & $pythonExe $targetPy --window $Window --verbose
}
else {
    Write-Host "AS_OF  : $AsOf"
    Write-Host "CMD    : $pythonExe $targetPy --window $Window --as-of $AsOf --verbose"
    Write-Host ""
    & $pythonExe $targetPy --window $Window --as-of $AsOf --verbose
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "build_sentiment_trend failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "build_sentiment_trend completed." -ForegroundColor Green
exit 0