param(
    [string]$Date = "",
    [string]$Root = "",
    [switch]$AllowDirtyRepo,
    [switch]$SkipMain,
    [switch]$SkipFx,
    [switch]$SkipHealth,
    [switch]$SkipRefresh,
    [switch]$ContinueOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host "[$ts] $Message"
}

function Resolve-RepoRoot {
    param([string]$ExplicitRoot)

    if (-not [string]::IsNullOrWhiteSpace($ExplicitRoot)) {
        return (Resolve-Path $ExplicitRoot).Path
    }

    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    if ($MyInvocation.MyCommand.Path) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        return (Resolve-Path (Join-Path $scriptDir "..")).Path
    }

    return (Get-Location).Path
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Log "=== $Name ==="
    try {
        & $Action
    }
    catch {
        if ($ContinueOnError) {
            Write-Warning "$Name failed: $($_.Exception.Message)"
        }
        else {
            throw
        }
    }
}

function Test-ScriptSupportsDate {
    param([string]$ScriptPath)

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        return $false
    }

    try {
        $text = Get-Content -LiteralPath $ScriptPath -Raw -Encoding UTF8
        if ($text -match '(?is)param\s*\(' -and $text -match '(?i)\$Date\b') {
            return $true
        }
    }
    catch {
        return $false
    }

    return $false
}

function Invoke-PowerShellFile {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string]$DateValue = "",
        [switch]$PassAllowDirtyRepo
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Log "[SKIP] missing script: $ScriptPath"
        return
    }

    $args = @(
        "-ExecutionPolicy", "Bypass",
        "-File", $ScriptPath
    )

    if (-not [string]::IsNullOrWhiteSpace($DateValue) -and (Test-ScriptSupportsDate -ScriptPath $ScriptPath)) {
        $args += @("-Date", $DateValue)
    }

    if ($PassAllowDirtyRepo) {
        $args += "-AllowDirtyRepo"
    }

    Write-Host ("CMD: powershell " + ($args -join " "))
    & powershell @args
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

$Root = Resolve-RepoRoot -ExplicitRoot $Root
if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Get-Date -Format "yyyy-MM-dd"
}

$scriptsDir = Join-Path $Root "scripts"

Write-Host "Morning Ritual (single entrypoint)"
Write-Host "ROOT      : $Root"
Write-Host "DATE      : $Date"
Write-Host ("GUARD     : " + ($(if ($AllowDirtyRepo) { "OFF" } else { "ON" })))
Write-Host ("MAIN      : " + ($(if ($SkipMain) { "SKIP" } else { "RUN" })))
Write-Host ("FX        : " + ($(if ($SkipFx) { "SKIP" } else { "RUN" })))
Write-Host ("HEALTH    : " + ($(if ($SkipHealth) { "SKIP" } else { "RUN" })))
Write-Host ("REFRESH   : " + ($(if ($SkipRefresh) { "SKIP" } else { "RUN" })))
Write-Host ""

Push-Location $Root
try {
    if (-not $AllowDirtyRepo) {
        $gitStatus = git status --porcelain 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($gitStatus | Out-String))) {
            throw "Working tree is not clean. Commit/stash changes or rerun with -AllowDirtyRepo."
        }
    }
    else {
        Write-Log "Dirty repo allowed by flag."
    }

    if (-not $SkipMain) {
        Invoke-Step -Name "1) run_daily_with_publish" -Action {
            Invoke-PowerShellFile `
                -Name "run_daily_with_publish" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_with_publish.ps1") `
                -DateValue $Date `
                -PassAllowDirtyRepo:$AllowDirtyRepo
        }
    }

    if (-not $SkipFx) {
        Invoke-Step -Name "FX Lane 1) Daily rates" -Action {
            Invoke-PowerShellFile `
                -Name "FX Lane 1) Daily rates" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_fx_rates.ps1") `
                -DateValue $Date
        }

        Invoke-Step -Name "FX Lane 2) Daily inputs" -Action {
            Invoke-PowerShellFile `
                -Name "FX Lane 2) Daily inputs" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_fx_inputs.ps1") `
                -DateValue $Date
        }

        Invoke-Step -Name "FX Lane 3) Daily overlay" -Action {
            Invoke-PowerShellFile `
                -Name "FX Lane 3) Daily overlay" `
                -ScriptPath (Join-Path $scriptsDir "run_daily_fx_overlay.ps1") `
                -DateValue $Date
        }
    }

    if (-not $SkipHealth) {
        Invoke-Step -Name "Health lane" -Action {
            Invoke-PowerShellFile `
                -Name "Health lane" `
                -ScriptPath (Join-Path $scriptsDir "run_health_checks.ps1") `
                -DateValue $Date
        }
    }

    if (-not $SkipRefresh) {
        Invoke-Step -Name "Refresh latest artifacts" -Action {
            $refreshCandidates = @(
                (Join-Path $scriptsDir "refresh_latest.ps1"),
                (Join-Path $scriptsDir "refresh_latest_artifacts.ps1"),
                (Join-Path $scriptsDir "materialize_latest.ps1")
            )

            $refreshScript = $refreshCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
            if ($null -eq $refreshScript -or [string]::IsNullOrWhiteSpace($refreshScript)) {
                Write-Log "[SKIP] refresh script not found."
                return
            }

            Invoke-PowerShellFile `
                -Name "Refresh latest artifacts" `
                -ScriptPath $refreshScript `
                -DateValue $Date
        }
    }

    Write-Log "Morning Ritual completed successfully."
    exit 0
}
catch {
    Write-Host "Morning Ritual finished with warnings/errors."
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
