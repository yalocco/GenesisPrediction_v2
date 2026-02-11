# scripts/run_daily_fx_overlay.ps1
# Build FX overlay PNG and publish into /analysis (for GUI)
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts\run_daily_fx_overlay.ps1
# Optional:
#   powershell -ExecutionPolicy Bypass -File scripts\run_daily_fx_overlay.ps1 -Date 2026-02-11
#   powershell -ExecutionPolicy Bypass -File scripts\run_daily_fx_overlay.ps1 -Strict

param(
  [switch]$Strict,
  [string]$Date
)

$ErrorActionPreference = "Stop"

function NowStr { (Get-Date).ToString("HH:mm:ss") }
function Stamp($msg) { Write-Host ("[{0}] {1}" -f (NowStr), $msg) }

if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = (Get-Date).ToString("yyyy-MM-dd")
}

$ROOT = (Resolve-Path ".").Path
Stamp "START FX overlay date=$Date strict=$Strict"
Stamp "ROOT: $ROOT"

$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (!(Test-Path $PY)) { $PY = "python" }

function Run-Py([string]$argsLine, [switch]$AllowFail) {
  Stamp ("PY  {0}" -f $argsLine)
  $p = Start-Process -FilePath $PY -ArgumentList $argsLine -NoNewWindow -Wait -PassThru
  if ($p.ExitCode -ne 0) {
    if ($AllowFail) {
      Stamp ("WARN step failed -> continue (exit={0})" -f $p.ExitCode)
      return $false
    }
    throw ("Python failed ({0}) exit={1}" -f $argsLine, $p.ExitCode)
  }
  return $true
}

# 1) Materialize rates (may fail if API key missing; overlay can still be built from cached data)
Run-Py "scripts\fx_materialize_rates.py" -AllowFail

# 2) Build today's remittance inputs
Run-Py "scripts\fx_remittance_today.py"

# 3) Build overlay PNG
Run-Py "scripts\fx_remittance_overlay.py"

# 4) Publish overlay PNG into analysis mount (requires --date)
Run-Py ("scripts\publish_fx_overlay_to_analysis.py --date {0}" -f $Date)

Stamp "DONE FX overlay"
