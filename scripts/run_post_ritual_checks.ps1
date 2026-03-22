param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
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

function Invoke-Step {
    param(
        [string]$Title,
        [string]$PythonExe,
        [string]$ScriptPath
    )

    Write-Section $Title
    Write-Host "CMD: $PythonExe $ScriptPath"

    # 標準出力をそのまま画面に流し、関数の戻り値には混ぜない
    & $PythonExe $ScriptPath | Out-Host
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
$VectorCheck = Join-Path $Root "scripts\check_vector_memory_freshness.py"
$VectorBuild = Join-Path $Root "scripts\build_vector_memory.py"

if (-not (Test-Path $DecisionCheck)) {
    throw "Missing script: $DecisionCheck"
}
if (-not (Test-Path $VectorCheck)) {
    throw "Missing script: $VectorCheck"
}
if (-not (Test-Path $VectorBuild)) {
    throw "Missing script: $VectorBuild"
}

Write-Host "GenesisPrediction - Post Ritual Checks"
Write-Host "ROOT   : $Root"
Write-Host "PYTHON : $PythonExe"

[int]$decisionStatus = Invoke-Step -Title "Decision Log Freshness Check" -PythonExe $PythonExe -ScriptPath $DecisionCheck
[int]$vectorStatus = Invoke-Step -Title "Vector Memory Freshness Check" -PythonExe $PythonExe -ScriptPath $VectorCheck

Write-Section "Post Ritual Summary"

if ($decisionStatus -eq 0) {
    Write-Host "[OK] decision_log.md looks current"
} else {
    Write-Host "[WARN] decision_log.md may need review"
    Write-Host "       Review docs/core/decision_log.md and record important human decisions if needed."
}

if ($vectorStatus -eq 0) {
    Write-Host "[OK] vector memory is fresh"
} else {
    Write-Host "[WARN] vector memory rebuild recommended"
    Write-Host "       Suggested command:"
    Write-Host "       $PythonExe $VectorBuild"
}

Write-Host ""
Write-Host "[DONE] Post ritual checks complete"
exit 0