<# 
Morning Ritual (single entrypoint)
UTC-aligned version: prevents JST/UTC date drift.
#>

param(
  [Parameter(Mandatory = $false)]
  [string]$Date
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function NowStamp {
  return (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
}

function Log([string]$msg) {
  Write-Host ("[{0}] {1}" -f (NowStamp), $msg)
}

function Fail([string]$msg) {
  Write-Host ("[{0}] [ERROR] {1}" -f (NowStamp), $msg) -ForegroundColor Red
  exit 1
}

# --- SAFE repo root resolution ---
function Resolve-RepoRoot {
  if ($PSScriptRoot) {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  }
  return (Resolve-Path "..").Path
}

# --- UTC Date normalization ---
function Ensure-Date([string]$d) {
  if ([string]::IsNullOrWhiteSpace($d)) {
    # Always use UTC date to align with analyzer/docker
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
  }
  $null = [DateTime]::ParseExact($d, "yyyy-MM-dd", $null)
  return $d
}

function Run-Pwsh([string]$title, [string]$ps1Path, [string[]]$psArgs) {
  $argStr = ""
  if ($psArgs -and $psArgs.Count -gt 0) { $argStr = ($psArgs -join " ") }

  Log "=== $title ==="
  Log ("CMD: powershell -ExecutionPolicy Bypass -File ""{0}"" {1}" -f $ps1Path, $argStr)

  & powershell -ExecutionPolicy Bypass -File $ps1Path @psArgs
  if ($LASTEXITCODE -ne 0) {
    Fail "$title failed (exit=$LASTEXITCODE)"
  }
}

function Run-Py([string]$title, [string]$pyExe, [string]$pyPath, [string[]]$pyArgs) {
  $argStr = ""
  if ($pyArgs -and $pyArgs.Count -gt 0) { $argStr = ($pyArgs -join " ") }

  Log "=== $title ==="
  Log ("CMD: ""{0}"" ""{1}"" {2}" -f $pyExe, $pyPath, $argStr)

  & $pyExe $pyPath @pyArgs
  if ($LASTEXITCODE -ne 0) {
    Fail "$title failed (exit=$LASTEXITCODE)"
  }
}

# -----------------------------
# Main
# -----------------------------
$ROOT = Resolve-RepoRoot
$Date = Ensure-Date $Date

Write-Host ""
Write-Host "Morning Ritual (single entrypoint)"
Write-Host ("ROOT      : {0}" -f $ROOT)
Write-Host ("DATE (UTC): {0}" -f $Date)
Write-Host ""

$py = Join-Path $ROOT ".venv\Scripts\python.exe"

try {

  # 1) Core daily pipeline
  Run-Pwsh "1) run_daily_with_publish" (Join-Path $ROOT "scripts\run_daily_with_publish.ps1") @("-Date", $Date)

  # 1-1) Summary
  Run-Py "1-1) Publish daily_summary_latest" $py (Join-Path $ROOT "scripts\publish_daily_summary_latest.py") @("--date", $Date)

  # 1-2) Sentiment
  Run-Py "1-2) Build daily sentiment" $py (Join-Path $ROOT "scripts\build_daily_sentiment.py") @("--date", $Date)
  Run-Py "1-3) Build sentiment timeseries csv" $py (Join-Path $ROOT "scripts\build_sentiment_timeseries_csv.py") @("--date", $Date)

  # 2) FX
  Run-Pwsh "2-1) FX Rates" (Join-Path $ROOT "scripts\run_daily_fx_rates.ps1") @()
  Run-Pwsh "2-2) FX Inputs" (Join-Path $ROOT "scripts\run_daily_fx_inputs.ps1") @()
  Run-Pwsh "2-3) FX Overlay" (Join-Path $ROOT "scripts\run_daily_fx_overlay.ps1") @()

  # 2-4) Legacy FX overlay
  Run-Py "2-4) Publish FX overlay legacy" $py (Join-Path $ROOT "scripts\publish_fx_overlay_legacy.py") @("--date", $Date)

  # 2-5) FX overlay variants
  Run-Pwsh "2-5) FX Overlay variants" (Join-Path $ROOT "scripts\run_daily_fx_overlay_variants.ps1") @("-Date", $Date)

  # 2-6) Observation artifacts
  Run-Py "2-6) Build observation artifacts" $py (Join-Path $ROOT "scripts\build_observation_artifacts.py") @("--date", $Date)

  # 3) Health
  Run-Py "3) Build Data Health" $py (Join-Path $ROOT "scripts\build_data_health.py") @("--date", $Date)

  Log "DONE Morning Ritual (UTC aligned)"
}
catch {
  Fail $_.Exception.Message
}