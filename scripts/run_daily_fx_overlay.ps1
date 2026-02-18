# scripts/run_daily_fx_overlay.ps1
# FX overlay pipeline (safe)
# - Dashboard update (non-fatal)
# - Remittance overlay (required)
# - Multi overlay (optional: skip if missing / continue if failed)
# - Publish to analysis + app/static (required)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-File {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (-not (Test-Path $Path)) { throw "[ERROR] missing file: $Path" }
}

function Invoke-External {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [Parameter(Mandatory=$true)][string[]]$Arguments
  )
  # Stream output to console, but ensure this function returns ONLY the exit code (int)
  & $Exe @Arguments | Out-Host
  return $LASTEXITCODE
}

function Invoke-ExternalOrThrow {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [Parameter(Mandatory=$true)][string[]]$Arguments
  )
  $code = Invoke-External -Exe $Exe -Arguments $Arguments
  if ($code -ne 0) {
    throw "[ERROR] command failed (exit=$code): $Exe $($Arguments -join ' ')"
  }
}

$REPO = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PY = Join-Path $REPO ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

$DATE = (Get-Date -Format "yyyy-MM-dd")
$ts = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts] START FX overlay date=$DATE"

# 1) Dashboard update（stale 等で落ちることがある → 非fatal）
$dash = Join-Path $REPO "scripts\fx_remittance_dashboard_update.py"
Require-File $dash
$codeDash = Invoke-External -Exe $PY -Arguments @($dash, "--date", $DATE)
if ($codeDash -ne 0) {
  Write-Host "[INFO] dashboard update failed (exit=$codeDash). Continue with existing dashboard CSV."
}

# 2) Remit overlay（JPY→THB）【必須】
$remit = Join-Path $REPO "scripts\fx_remittance_overlay.py"
Require-File $remit
Invoke-ExternalOrThrow -Exe $PY -Arguments @($remit)

# 3) Multi overlay（JPY↔USD 等）【任意】
$multi = Join-Path $REPO "scripts\fx_multi_overlay_from_rates.py"
if (-not (Test-Path $multi)) {
  Write-Host "[INFO] multi overlay script missing (skipped): $multi"
} else {
  $codeMulti = Invoke-External -Exe $PY -Arguments @($multi, "--repo", $REPO, "--period", "90")
  if ($codeMulti -ne 0) {
    Write-Host "[INFO] multi overlay failed (exit=$codeMulti). Continue without multi overlay."
  } else {
    Write-Host "[OK] multi overlay built"
  }
}

# 4) Publish（analysis + app/static）【必須】
$pub = Join-Path $REPO "scripts\publish_fx_overlay_to_analysis.py"
Require-File $pub
Invoke-ExternalOrThrow -Exe $PY -Arguments @($pub, "--date", $DATE, "--pair", "both")

$ts2 = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts2] DONE FX overlay"
