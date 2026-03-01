# scripts/run_morning_ritual.ps1
# Morning Ritual (single entrypoint)
# Goal: One command to converge analysis health to OK (OK=10/WARN=0/NG=0) with minimal, reproducible steps.
# Notes:
# - WorldDate is UTC date string (yyyy-MM-dd) used as the ritual's single truth.
# - FX scripts may use local dates internally; ritual reconciles artifacts so health can be OK for WorldDate.

[CmdletBinding()]
param(
  # WorldDate (UTC) in yyyy-MM-dd. Default: (Get-Date).ToUniversalTime() date string.
  [Parameter(Mandatory=$false)]
  [string]$Date,

  # If specified, pass -RunGuard to run_daily_with_publish.ps1
  [switch]$RunGuard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowIso() {
  return (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
}

function Log([string]$msg) {
  Write-Host ("[{0}] {1}" -f (NowIso), $msg)
}

function Fail([string]$step, [string]$detail, [int]$exitCode = 1) {
  Log ("[ERROR] {0} failed (exit={1})" -f $step, $exitCode)
  Log ("[ERROR] {0}" -f $detail)
  exit $exitCode
}

function Run([string]$step, [scriptblock]$action) {
  try {
    & $action
  } catch {
    Fail $step ($_.Exception.Message) 1
  }
}

# --- Resolve dates ---
$repoRoot = (Resolve-Path ".").Path
$utcNow = (Get-Date).ToUniversalTime()

if ([string]::IsNullOrWhiteSpace($Date)) {
  $WorldDate = $utcNow.ToString("yyyy-MM-dd")
} else {
  $WorldDate = $Date.Trim()
}

$LocalDate = (Get-Date).ToString("yyyy-MM-dd")

Log "Morning Ritual (single entrypoint)"
Write-Host ("ROOT : {0}" -f $repoRoot)
Write-Host ("DATE (UTC): {0}" -f $WorldDate)

# Common paths
$py = Join-Path $repoRoot ".venv\Scripts\python.exe"

# --- 1) Main pipeline ---
Run "1) run_daily_with_publish" {
  Log "=== 1) run_daily_with_publish ==="
  $cmd = "powershell -ExecutionPolicy Bypass -File `"$repoRoot\scripts\run_daily_with_publish.ps1`" -Date $WorldDate"
  if ($RunGuard) { $cmd += " -RunGuard" }
  Log "CMD: $cmd"
  if ($RunGuard) {
    powershell -ExecutionPolicy Bypass -File "$repoRoot\scripts\run_daily_with_publish.ps1" -Date $WorldDate -RunGuard
  } else {
    powershell -ExecutionPolicy Bypass -File "$repoRoot\scripts\run_daily_with_publish.ps1" -Date $WorldDate
  }
}

# --- 1-1) Publish daily_summary_latest (explicit) ---
Run "1-1) Publish daily_summary_latest" {
  Log "=== 1-1) Publish daily_summary_latest ==="
  $cmd = "`"$py`" `"$repoRoot\scripts\publish_daily_summary_latest.py`" --date $WorldDate"
  Log "CMD: $cmd"
  & $py "$repoRoot\scripts\publish_daily_summary_latest.py" --date $WorldDate
}

# --- 1-2) Build daily sentiment ---
Run "1-2) Build daily sentiment" {
  Log "=== 1-2) Build daily sentiment ==="
  $cmd = "`"$py`" `"$repoRoot\scripts\build_daily_sentiment.py`" --date $WorldDate"
  Log "CMD: $cmd"
  & $py "$repoRoot\scripts\build_daily_sentiment.py" --date $WorldDate
}

# --- 1-3) Build sentiment timeseries csv ---
Run "1-3) Build sentiment timeseries csv" {
  Log "=== 1-3) Build sentiment timeseries csv ==="
  $cmd = "`"$py`" `"$repoRoot\scripts\build_sentiment_timeseries_csv.py`" --date $WorldDate"
  Log "CMD: $cmd"
  & $py "$repoRoot\scripts\build_sentiment_timeseries_csv.py" --date $WorldDate
}

# --- 2-1) FX Rates ---
Run "2-1) FX Rates" {
  Log "=== 2-1) FX Rates ==="
  $cmd = "powershell -ExecutionPolicy Bypass -File `"$repoRoot\scripts\run_daily_fx_rates.ps1`""
  Log "CMD: $cmd"
  powershell -ExecutionPolicy Bypass -File "$repoRoot\scripts\run_daily_fx_rates.ps1"
}

# --- 2-2) FX Inputs ---
Run "2-2) FX Inputs" {
  Log "=== 2-2) FX Inputs ==="
  $cmd = "powershell -ExecutionPolicy Bypass -File `"$repoRoot\scripts\run_daily_fx_inputs.ps1`""
  Log "CMD: $cmd"
  powershell -ExecutionPolicy Bypass -File "$repoRoot\scripts\run_daily_fx_inputs.ps1"
}

# --- 2-3) FX Overlay ---
Run "2-3) FX Overlay" {
  Log "=== 2-3) FX Overlay ==="
  $cmd = "powershell -ExecutionPolicy Bypass -File `"$repoRoot\scripts\run_daily_fx_overlay.ps1`""
  Log "CMD: $cmd"
  powershell -ExecutionPolicy Bypass -File "$repoRoot\scripts\run_daily_fx_overlay.ps1"
}

# --- 2-4) Reconcile FX dated artifacts for WorldDate and publish legacy ---
Run "2-4) Publish FX overlay legacy (converge)" {
  Log "=== 2-4) Publish FX overlay legacy (converge) ==="

  $analysisDir = Join-Path $repoRoot "data\world_politics\analysis"
  $srcWorld = Join-Path $analysisDir ("fx_jpy_thb_overlay_{0}.png" -f $WorldDate)
  $srcLocal = Join-Path $analysisDir ("fx_jpy_thb_overlay_{0}.png" -f $LocalDate)

  # If WorldDate source is missing but LocalDate exists, copy LocalDate -> WorldDate
  if (-not (Test-Path $srcWorld)) {
    if (Test-Path $srcLocal) {
      Log ("[WARN] missing {0} ; copying from local-dated {1}" -f (Split-Path $srcWorld -Leaf), (Split-Path $srcLocal -Leaf))
      Copy-Item -Force $srcLocal $srcWorld
      Log ("[OK] created missing world-dated overlay: {0}" -f (Split-Path $srcWorld -Leaf))
    } else {
      # If both are missing, try to proceed to publish (it will fail with clear error)
      Log ("[WARN] missing both world/local source overlays: {0} / {1}" -f (Split-Path $srcWorld -Leaf), (Split-Path $srcLocal -Leaf))
    }
  }

  # Publish legacy for WorldDate (this creates fx_overlay_YYYY-MM-DD.png)
  $cmd = "`"$py`" `"$repoRoot\scripts\publish_fx_overlay_legacy.py`" --date $WorldDate"
  Log "CMD: $cmd"
  & $py "$repoRoot\scripts\publish_fx_overlay_legacy.py" --date $WorldDate
}

# --- 3) Observation artifacts (keep health clean) ---
Run "3) Build observation artifacts" {
  Log "=== 3) Build observation artifacts ==="
  $script = Join-Path $repoRoot "scripts\build_observation_artifacts.py"
  if (Test-Path $script) {
    $cmd = "`"$py`" `"$script`" --date $WorldDate"
    Log "CMD: $cmd"
    & $py $script --date $WorldDate
  } else {
    Log "[WARN] scripts\build_observation_artifacts.py not found; skipping"
  }
}

# --- 4) Data Health update (must be WorldDate) ---
Run "4) Data Health update" {
  Log "=== 4) Data Health update ==="
  $cmd = "`"$py`" `"$repoRoot\scripts\build_data_health.py`" --date $WorldDate"
  Log "CMD: $cmd"
  & $py "$repoRoot\scripts\build_data_health.py" --date $WorldDate
}

Log "DONE (Morning Ritual)"
exit 0