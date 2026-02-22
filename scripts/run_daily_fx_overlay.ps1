# scripts/run_daily_fx_overlay.ps1
# FX overlay pipeline (safe)
# - Dashboard update (non-fatal)  ※週末は「前営業日」を使う
# - Sanitize dashboard CSV (self-healing)  ※壊れた行があっても復旧
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

  # DayOfWeek: Sunday=0, Monday=1, ..., Saturday=6
  if ($d.DayOfWeek -eq [System.DayOfWeek]::Saturday) {
    $d = $d.AddDays(-1)
  } elseif ($d.DayOfWeek -eq [System.DayOfWeek]::Sunday) {
    $d = $d.AddDays(-2)
  }

  return $d.ToString("yyyy-MM-dd")
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

    # Try robust read: python engine + skip bad lines.
    # Support both new and old pandas APIs.
    try:
        df = pd.read_csv(p, engine="python", on_bad_lines="skip")
    except TypeError:
        # older pandas
        df = pd.read_csv(p, engine="python", error_bad_lines=False, warn_bad_lines=True)

    # Normalize: write back with consistent quoting
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

# Ritual date (used for publishing dated artifacts)
$DATE = (Get-Date -Format "yyyy-MM-dd")

# FX effective date (used for rate-dependent checks on weekends)
$FX_DATE = Get-LastBusinessDayString -Ymd $DATE
if ($FX_DATE -ne $DATE) {
  Write-Host ("[INFO] FX date adjusted (weekend): {0} -> {1}" -f $DATE, $FX_DATE)
}

$ts = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts] START FX overlay date=$DATE (fx_date=$FX_DATE)"

# 1) Dashboard update（stale 等で落ちることがある → 非fatal）
#    IMPORTANT: use $FX_DATE so weekends don't demand non-existent rates.
$dash = Join-Path $REPO "scripts\fx_remittance_dashboard_update.py"
Require-File $dash
$codeDash = Invoke-External -Exe $PY -Arguments @($dash, "--date", $FX_DATE)
if ($codeDash -ne 0) {
  Write-Host "[INFO] dashboard update failed (exit=$codeDash). Continue with existing dashboard CSV."
}

# 1.5) Sanitize dashboard CSV (self-healing)
#      Fixes sporadic CSV corruption: "Expected N fields ... saw M"
$dashboardCsv = Join-Path $REPO "data\fx\jpy_thb_remittance_dashboard.csv"
Sanitize-DashboardCsv -PythonExe $PY -CsvPath $dashboardCsv

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
#    IMPORTANT: publish uses the ritual $DATE (e.g., news date),
#    even if underlying rates are from $FX_DATE on weekends.
$pub = Join-Path $REPO "scripts\publish_fx_overlay_to_analysis.py"
Require-File $pub
Invoke-ExternalOrThrow -Exe $PY -Arguments @($pub, "--date", $DATE, "--pair", "both")

$ts2 = Get-Date -Format "HH:mm:ss"
Write-Host "[$ts2] DONE FX overlay"