# scripts/run_daily_fx_overlay.ps1
# FX overlay pipeline (safe / unified)
# - Dashboard update (non-fatal)
#   * weekend aware
#   * aligns fx_date to latest common availability in local rate CSVs
# - Sanitize dashboard CSV (self-healing)
# - Pair overlays (required)
#   * JPY→THB
#   * JPY→USD
# - Multi/pair overlays from raw rates (optional but recommended)
#   * fx_multi_overlay.png
#   * fx_multi_jpy_usd_overlay.png
#   * fx_multi_usd_thb_overlay.png
# - Variant overlays (required for served FX latest images)
#   * analysis/fx/fx_overlay_latest_*.png
#   * data/world_politics/analysis/fx/fx_overlay_latest_*.png
# - Publish legacy analysis overlays (required)
#   * fx_jpy_thb_overlay.png
#   * fx_jpy_usd_overlay.png

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

function Get-LastBusinessDayString {
  param([Parameter(Mandatory=$true)][string]$Ymd)

  $d = [datetime]::ParseExact($Ymd, "yyyy-MM-dd", $null)

  if ($d.DayOfWeek -eq [System.DayOfWeek]::Saturday) {
    $d = $d.AddDays(-1)
  } elseif ($d.DayOfWeek -eq [System.DayOfWeek]::Sunday) {
    $d = $d.AddDays(-2)
  }

  return $d.ToString("yyyy-MM-dd")
}

function Get-MaxDateFromRateCsv {
  param([Parameter(Mandatory=$true)][string]$CsvPath)

  if (-not (Test-Path $CsvPath)) {
    return $null
  }

  try {
    $rows = Import-Csv -Path $CsvPath
    if ($null -eq $rows -or $rows.Count -eq 0) { return $null }

    $last = $rows[-1].date
    if ([string]::IsNullOrWhiteSpace($last)) { return $null }

    [void][datetime]::ParseExact($last, "yyyy-MM-dd", $null)
    return $last
  } catch {
    return $null
  }
}

function Min-Ymd {
  param(
    [Parameter(Mandatory=$true)][string]$A,
    [Parameter(Mandatory=$true)][string]$B
  )
  $da = [datetime]::ParseExact($A, "yyyy-MM-dd", $null)
  $db = [datetime]::ParseExact($B, "yyyy-MM-dd", $null)
  if ($da -le $db) { return $A } else { return $B }
}

function Nz {
  param(
    [Parameter(Mandatory=$false)]$Value,
    [Parameter(Mandatory=$true)][string]$Fallback
  )
  if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) { return $Fallback }
  return [string]$Value
}

function Sanitize-DashboardCsv {
  param(
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [Parameter(Mandatory=$true)][string]$CsvPath
  )

  if (-not (Test-Path $CsvPath)) {
    Write-Host "[INFO] dashboard csv missing (skip sanitize): $CsvPath"
    return
  }

  $py = @'
import argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"[INFO] missing: {p}")
        return 0

    import pandas as pd

    try:
        df = pd.read_csv(p, engine="python", on_bad_lines="skip")
    except TypeError:
        df = pd.read_csv(p, engine="python", error_bad_lines=False, warn_bad_lines=True)

    tmp = p.with_suffix(p.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(p)
    print(f"[OK] sanitized dashboard csv: {p} (rows={len(df)})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'@

  $tmpPy = Join-Path $env:TEMP ("sanitize_fx_dashboard_{0}.py" -f ([Guid]::NewGuid().ToString("N")))
  Set-Content -Path $tmpPy -Value $py -Encoding UTF8

  try {
    $code = Invoke-External -Exe $PythonExe -Arguments @($tmpPy, "--path", $CsvPath)
    if ($code -ne 0) {
      Write-Host "[WARN] sanitize failed (exit=$code). Continue with existing CSV: $CsvPath"
    }
  } finally {
    Remove-Item -Path $tmpPy -Force -ErrorAction SilentlyContinue | Out-Null
  }
}

$REPO = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PY = Join-Path $REPO ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { $PY = "python" }

$DATE = (Get-Date -Format "yyyy-MM-dd")
$FX_DATE = Get-LastBusinessDayString -Ymd $DATE

$usdthbCsv = Join-Path $REPO "data\fx\usdthb.csv"
$usdjpyCsv = Join-Path $REPO "data\fx\usdjpy.csv"

$usdthbMax = Get-MaxDateFromRateCsv -CsvPath $usdthbCsv
$usdjpyMax = Get-MaxDateFromRateCsv -CsvPath $usdjpyCsv

if ($usdthbMax -and $usdjpyMax) {
  $commonMax = Min-Ymd -A $usdthbMax -B $usdjpyMax
  $FX_DATE = Min-Ymd -A $FX_DATE -B $commonMax
}

if ($FX_DATE -ne $DATE) {
  Write-Host ("[INFO] FX date effective: {0} -> {1} (usdthb_max={2} usdjpy_max={3})" -f $DATE, $FX_DATE, (Nz $usdthbMax "n/a"), (Nz $usdjpyMax "n/a"))
}

$ts = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts] START FX overlay date=$DATE (fx_date=$FX_DATE)"

# 1) Dashboard update (non-fatal, THB legacy support)
$dash = Join-Path $REPO "scripts\fx_remittance_dashboard_update.py"
Require-File $dash
$codeDash = Invoke-External -Exe $PY -Arguments @($dash, "--date", $FX_DATE)
if ($codeDash -ne 0) {
  Write-Host "[INFO] dashboard update failed (exit=$codeDash). Continue with existing dashboard CSV."
}

# 1.5) Sanitize dashboard CSVs
$dashboardCsvLegacy = Join-Path $REPO "data\fx\jpy_thb_remittance_dashboard.csv"
$dashboardCsvPairThb = Join-Path $REPO "data\fx\dashboard\jpy_thb_dashboard.csv"
$dashboardCsvPairUsd = Join-Path $REPO "data\fx\dashboard\jpy_usd_dashboard.csv"

Sanitize-DashboardCsv -PythonExe $PY -CsvPath $dashboardCsvLegacy
Sanitize-DashboardCsv -PythonExe $PY -CsvPath $dashboardCsvPairThb
Sanitize-DashboardCsv -PythonExe $PY -CsvPath $dashboardCsvPairUsd

# 2) Pair overlays (required)
$remit = Join-Path $REPO "scripts\fx_remittance_overlay.py"
Require-File $remit

# JPY -> THB
Invoke-ExternalOrThrow -Exe $PY -Arguments @($remit, "--pair", "jpy_thb")

# JPY -> USD
Invoke-ExternalOrThrow -Exe $PY -Arguments @($remit, "--pair", "jpy_usd")

# 3) Multi/pair overlays from raw rates (optional but recommended)
$multi = Join-Path $REPO "scripts\fx_multi_overlay_from_rates.py"
if (-not (Test-Path $multi)) {
  Write-Host "[INFO] multi overlay script missing (skipped): $multi"
} else {
  $codeMulti = Invoke-External -Exe $PY -Arguments @($multi)
  if ($codeMulti -ne 0) {
    Write-Host "[INFO] multi overlay failed (exit=$codeMulti). Continue without multi overlay variants."
  } else {
    Write-Host "[OK] multi overlay built"
  }
}

# 4) FX variant overlays (required for USDJPY/USDTHB latest served images)
$variants = Join-Path $REPO "scripts\build_fx_overlay_variants.py"
if (-not (Test-Path $variants)) {
  throw "[ERROR] missing file: $variants"
} else {
  Invoke-ExternalOrThrow -Exe $PY -Arguments @($variants, "--date", $DATE)
  Write-Host "[OK] fx overlay variants built"
}

# 5) Publish legacy analysis overlays (required)
$pub = Join-Path $REPO "scripts\publish_fx_overlay_to_analysis.py"
Require-File $pub
Invoke-ExternalOrThrow -Exe $PY -Arguments @($pub, "--date", $DATE, "--pair", "both")

$ts2 = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts2] DONE FX overlay"