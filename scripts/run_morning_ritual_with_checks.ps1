param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Date = ""
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host ""
    Write-Host "[$ts] === $Message ==="
}

# -----------------------------
# Resolve paths
# -----------------------------
$Root = (Resolve-Path $Root).Path
$MorningRitual = Join-Path $Root "scripts\run_morning_ritual.ps1"
$PostChecks = Join-Path $Root "scripts\run_post_ritual_checks.ps1"

if (-not (Test-Path $MorningRitual)) {
    throw "Missing script: $MorningRitual"
}

if (-not (Test-Path $PostChecks)) {
    throw "Missing script: $PostChecks"
}

Write-Host "GenesisPrediction - Morning Ritual (with Post Checks)"
Write-Host "ROOT : $Root"

if ($Date -ne "") {
    Write-Host "DATE : $Date"
}

# -----------------------------
# 1) Run original Morning Ritual
# -----------------------------
Write-Section "Run Morning Ritual"

if ($Date -ne "") {
    Write-Host "CMD: powershell -ExecutionPolicy Bypass -File $MorningRitual -Date $Date"
    powershell -ExecutionPolicy Bypass -File $MorningRitual -Date $Date
} else {
    Write-Host "CMD: powershell -ExecutionPolicy Bypass -File $MorningRitual"
    powershell -ExecutionPolicy Bypass -File $MorningRitual
}

$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    throw "Morning Ritual failed with exit code $exitCode"
}

# -----------------------------
# 2) Run Post Ritual Checks
# -----------------------------
Write-Section "Run Post Ritual Checks"

Write-Host "CMD: powershell -ExecutionPolicy Bypass -File $PostChecks"
powershell -ExecutionPolicy Bypass -File $PostChecks

$exitCode = $LASTEXITCODE

if ($exitCode -ne 0 -and $exitCode -ne 2) {
    throw "Post Ritual Checks failed with exit code $exitCode"
}

# -----------------------------
# Done
# -----------------------------
Write-Section "All Complete"

Write-Host "[DONE] Morning Ritual + Post Checks complete"
exit 0
