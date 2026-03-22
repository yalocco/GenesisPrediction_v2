param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$AutoRebuildVectorMemory = $true,
    [switch]$ForceRebuildVectorMemory = $false
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host ""
    Write-Host "[$ts] === $Message ==="
}

function Resolve-Python {
    param([string]$RepoRoot)

    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        "python"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") {
            return $candidate
        }
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Python executable not found."
}

function Invoke-PythonStep {
    param(
        [string]$Title,
        [string]$PythonExe,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    Write-Section $Title

    $argText = @($ScriptPath) + $Arguments
    Write-Host "CMD: $PythonExe $($argText -join ' ')"

    & $PythonExe $ScriptPath @Arguments | Out-Host
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "[OK] $Title"
        return 0
    }

    if ($exitCode -eq 2) {
        Write-Host "[WARN] $Title reported attention needed"
        return 2
    }

    throw "$Title failed with exit code $exitCode"
}

$Root = (Resolve-Path $Root).Path
$PythonExe = Resolve-Python -RepoRoot $Root

$DecisionCheck = Join-Path $Root "scripts\check_decision_log_freshness.py"
$VectorCheck   = Join-Path $Root "scripts\check_vector_memory_freshness.py"
$VectorBuild   = Join-Path $Root "scripts\build_vector_memory.py"

foreach ($required in @($DecisionCheck, $VectorCheck, $VectorBuild)) {
    if (-not (Test-Path $required)) {
        throw "Missing script: $required"
    }
}

Write-Host "GenesisPrediction - Post Ritual Checks"
Write-Host "ROOT   : $Root"
Write-Host "PYTHON : $PythonExe"
Write-Host "AUTO   : VectorMemoryRebuild=$AutoRebuildVectorMemory"
Write-Host "FORCE  : VectorMemoryRebuild=$ForceRebuildVectorMemory"

[int]$decisionStatus = Invoke-PythonStep `
    -Title "Decision Log Freshness Check" `
    -PythonExe $PythonExe `
    -ScriptPath $DecisionCheck

[int]$vectorStatus = Invoke-PythonStep `
    -Title "Vector Memory Freshness Check" `
    -PythonExe $PythonExe `
    -ScriptPath $VectorCheck

$vectorRebuildRan = $false
$vectorFinalStatus = $vectorStatus

$shouldRebuild = $false

if ($ForceRebuildVectorMemory) {
    $shouldRebuild = $true
}
elseif ($vectorStatus -eq 2 -and $AutoRebuildVectorMemory) {
    $shouldRebuild = $true
}

if ($shouldRebuild) {
    Write-Section "Auto Rebuild Vector Memory"

    if ($ForceRebuildVectorMemory) {
        Write-Host "[INFO] Force rebuild requested."
    }
    elseif ($vectorStatus -eq 2) {
        Write-Host "[INFO] Vector memory freshness check returned WARN."
    }

    Write-Host "[INFO] Running automatic rebuild with --recreate."

    [int]$buildStatus = Invoke-PythonStep `
        -Title "Vector Memory Build (--recreate)" `
        -PythonExe $PythonExe `
        -ScriptPath $VectorBuild `
        -Arguments @("--recreate")

    if ($buildStatus -ne 0) {
        throw "Vector Memory Build (--recreate) did not complete successfully."
    }

    $vectorRebuildRan = $true

    [int]$vectorFinalStatus = Invoke-PythonStep `
        -Title "Vector Memory Freshness Re-Check" `
        -PythonExe $PythonExe `
        -ScriptPath $VectorCheck
}

Write-Section "Post Ritual Summary"

if ($decisionStatus -eq 0) {
    Write-Host "[OK] decision_log.md looks current"
}
else {
    Write-Host "[WARN] decision_log.md may need review"
    Write-Host "       Review docs/core/decision_log.md and record important human decisions if needed."
}

if ($vectorFinalStatus -eq 0) {
    if ($vectorRebuildRan) {
        Write-Host "[OK] vector memory rebuilt and is now fresh"
    }
    else {
        Write-Host "[OK] vector memory is fresh"
    }
}
else {
    Write-Host "[WARN] vector memory rebuild recommended"
    Write-Host "       Suggested command:"
    Write-Host "       $PythonExe $VectorBuild --recreate"
}

if ($vectorRebuildRan) {
    Write-Host "[INFO] automatic vector memory rebuild was performed"
}

Write-Host ""
Write-Host "[DONE] Post ritual checks complete"
exit 0