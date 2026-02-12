Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Exe {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [Parameter(Mandatory=$true)][string[]]$Arguments
  )
  & $Exe @Arguments
  return $LASTEXITCODE
}

function Invoke-ExeOrThrow {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [Parameter(Mandatory=$true)][string[]]$Arguments
  )
  & $Exe @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "[ERROR] command failed (exit=$LASTEXITCODE): $Exe $($Arguments -join ' ')"
  }
}

$REPO = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PY = Join-Path $REPO ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

$DATE = (Get-Date -Format "yyyy-MM-dd")

function Require-File {
  param([string]$Path)
  if (-not (Test-Path $Path)) { throw "[ERROR] missing file: $Path" }
}

$ts = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts] START FX overlay date=$DATE"

# 1) Dashboard update（rates stale 等で落ちることがある → 非fatal）
$dash = Join-Path $REPO "scripts\fx_remittance_dashboard_update.py"
Require-File $dash
$code = Invoke-Exe -Exe $PY -Arguments @($dash, "--date", $DATE)
if ($code -ne 0) {
  Write-Host "[WARN] dashboard update failed (exit=$code). Continue with existing dashboard CSV."
}

# 2) Remit overlay（JPY→THB）
$remit = Join-Path $REPO "scripts\fx_remittance_overlay.py"
Require-File $remit
Invoke-ExeOrThrow -Exe $PY -Arguments @($remit)

# 3) Multi overlay（rates から生成）
$multi = Join-Path $REPO "scripts\fx_multi_overlay_from_rates.py"
Require-File $multi
Invoke-ExeOrThrow -Exe $PY -Arguments @($multi, "--repo", $REPO, "--period", "90")

# 4) Publish（analysis + app/static）
$pub = Join-Path $REPO "scripts\publish_fx_overlay_to_analysis.py"
Require-File $pub
Invoke-ExeOrThrow -Exe $PY -Arguments @($pub, "--repo", $REPO)

$ts2 = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts2] DONE FX overlay"