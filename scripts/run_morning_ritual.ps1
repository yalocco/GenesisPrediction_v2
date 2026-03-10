[CmdletBinding()]
param(
    [string]$Date = "",
    [switch]$Guard,
    [switch]$SkipMain,
    [switch]$SkipFx,
    [switch]$SkipHealth,
    [switch]$SkipRefresh,
    [switch]$ContinueOnError,
    [switch]$AllowDirtyRepo
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    Write-Host "[$ts] $Message"
}

function Resolve-Python {
    $candidates = @(
        (Join-Path $Root ".venv/Scripts/python.exe"),
        (Join-Path $Root ".venv/bin/python"),
        "python",
        "py"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python" -or $candidate -eq "py") {
            $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($null -ne $cmd) {
                return $candidate
            }
        }
        elseif (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Python runtime was not found. Expected .venv or PATH python."
}

function Fail-Or-Continue {
    param([string]$Message)
    if ($ContinueOnError) {
        Write-Warning $Message
    }
    else {
        throw $Message
    }
}

function Invoke-External {
    param(
        [string]$Title,
        [string[]]$Command,
        [string]$WorkingDirectory = $Root,
        [switch]$Optional
    )

    Write-Log "=== $Title ==="
    Write-Host ("CMD: " + ($Command -join " "))

    Push-Location $WorkingDirectory
    try {
        & $Command[0] @($Command[1..($Command.Length - 1)])
        if ($LASTEXITCODE -ne 0) {
            $message = "$Title failed with exit code $LASTEXITCODE."
            if ($Optional) {
                Fail-Or-Continue $message
            }
            else {
                throw $message
            }
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-PythonScript {
    param(
        [string]$Title,
        [string]$ScriptPath,
        [string[]]$Arguments = @(),
        [switch]$Optional
    )

    if (-not (Test-Path $ScriptPath)) {
        $message = "$Title skipped: script not found -> $ScriptPath"
        if ($Optional) {
            Write-Log $message
            return
        }
        throw $message
    }

    $python = Resolve-Python
    $cmd = @($python, $ScriptPath) + $Arguments
    Invoke-External -Title $Title -Command $cmd -Optional:$Optional
}

function Get-DefaultDate {
    return (Get-Date).ToString("yyyy-MM-dd")
}

function Test-GitClean {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $git) {
        Write-Log "git command not found; skip clean-check."
        return $true
    }

    $status = & git status --porcelain 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "git status check failed; skip clean-check."
        return $true
    }

    return [string]::IsNullOrWhiteSpace(($status | Out-String))
}

if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Get-DefaultDate
}

$mainEntry = Join-Path $ScriptDir "run_daily_with_publish.ps1"
$healthScript = Join-Path $Root "scripts/build_data_health.py"
$refreshScript = Join-Path $Root "scripts/refresh_latest_artifacts.py"

$fxSteps = @(
    @{ Title = "FX Lane 1) Daily rates"; Script = (Join-Path $ScriptDir "run_daily_fx_rates.ps1"); Args = @("-Date", $Date) },
    @{ Title = "FX Lane 2) Daily inputs"; Script = (Join-Path $ScriptDir "run_daily_fx_inputs.ps1"); Args = @("-Date", $Date) },
    @{ Title = "FX Lane 3) Daily overlay"; Script = (Join-Path $ScriptDir "run_daily_fx_overlay.ps1"); Args = @("-Date", $Date) }
)

Write-Host ""
Write-Host "Morning Ritual (single entrypoint)"
Write-Host "ROOT      : $Root"
Write-Host "DATE      : $Date"
Write-Host "GUARD     : $([string]::new($(if ($Guard) { 'ON' } else { 'OFF' })))"
Write-Host "MAIN      : $([string]::new($(if ($SkipMain) { 'SKIP' } else { 'RUN' })))"
Write-Host "FX        : $([string]::new($(if ($SkipFx) { 'SKIP' } else { 'RUN' })))"
Write-Host "HEALTH    : $([string]::new($(if ($SkipHealth) { 'SKIP' } else { 'RUN' })))"
Write-Host "REFRESH   : $([string]::new($(if ($SkipRefresh) { 'SKIP' } else { 'RUN' })))"
Write-Host ""

if (-not $AllowDirtyRepo) {
    if (-not (Test-GitClean)) {
        throw "Working tree is not clean. Commit/stash changes or rerun with -AllowDirtyRepo."
    }
}
else {
    Write-Log "Dirty repo allowed by flag."
}

$pipelineFailed = $false

try {
    if (-not $SkipMain) {
        if (-not (Test-Path $mainEntry)) {
            throw "Main entrypoint not found: $mainEntry"
        }

        $mainCmd = @(
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", $mainEntry,
            "-Date", $Date
        )

        if ($Guard) {
            $mainCmd += "-Guard"
        }
        if ($ContinueOnError) {
            $mainCmd += "-ContinueOnError"
        }

        Invoke-External -Title "1) run_daily_with_publish" -Command $mainCmd
    }
    else {
        Write-Log "Main lane skipped by flag."
    }

    if (-not $SkipFx) {
        foreach ($step in $fxSteps) {
            if (Test-Path $step.Script) {
                $cmd = @(
                    "powershell",
                    "-ExecutionPolicy", "Bypass",
                    "-File", $step.Script
                ) + $step.Args
                Invoke-External -Title $step.Title -Command $cmd -Optional
            }
            else {
                Write-Log ($step.Title + " skipped: script not found -> " + $step.Script)
            }
        }
    }
    else {
        Write-Log "FX lane skipped by flag."
    }

    if (-not $SkipHealth) {
        Invoke-PythonScript -Title "2) Build data health" -ScriptPath $healthScript -Arguments @("--root", $Root) -Optional
    }
    else {
        Write-Log "Health step skipped by flag."
    }

    if (-not $SkipRefresh) {
        Invoke-PythonScript -Title "3) Refresh latest artifacts" -ScriptPath $refreshScript -Arguments @() -Optional
    }
    else {
        Write-Log "Refresh step skipped by flag."
    }

    Write-Host ""
    Write-Host "Morning Ritual completed."
    Write-Host ""
}
catch {
    $pipelineFailed = $true
    Write-Error $_
    if (-not $ContinueOnError) {
        exit 1
    }
}
finally {
    if ($pipelineFailed) {
        Write-Host "Morning Ritual finished with warnings/errors."
    }
}
