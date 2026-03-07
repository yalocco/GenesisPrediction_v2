# scripts/run_labos_publish.ps1
# Build LABOS deploy payload and publish it in one step.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/run_labos_publish.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_labos_publish.ps1 -Profile prod
#   powershell -ExecutionPolicy Bypass -File scripts/run_labos_publish.ps1 -SkipBuild
#   powershell -ExecutionPolicy Bypass -File scripts/run_labos_publish.ps1 -DryRun
#
[CmdletBinding()]
param(
  [ValidateSet("dev","prod")]
  [string]$Profile = "dev",

  [string]$OutDir = "dist\labos_deploy",

  [switch]$SkipBuild,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Ok([string]$msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail([string]$msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$buildScript = Join-Path $PSScriptRoot "build_labos_deploy_payload.ps1"
$deployScript = Join-Path $PSScriptRoot "run_deploy_labos.ps1"

Info "GenesisPrediction v2 - LABOS Publish"
Info "RepoRoot : $repoRoot"
Info "Profile  : $Profile"
Info "OutDir   : $OutDir"
Info ("DryRun   : {0}" -f $DryRun.IsPresent)
Info ("SkipBuild: {0}" -f $SkipBuild.IsPresent)

if (-not (Test-Path $buildScript)) { Fail "missing build script: $buildScript" }
if (-not (Test-Path $deployScript)) { Fail "missing deploy runner: $deployScript" }

try {
  if (-not $SkipBuild) {
    Info "=== 1) Build deploy payload ==="
    & powershell -ExecutionPolicy Bypass -File $buildScript -OutDir $OutDir
    if ($LASTEXITCODE -ne 0) {
      Fail "build_labos_deploy_payload.ps1 failed (exit=$LASTEXITCODE)"
    }
    Ok "Deploy payload built"
  }
  else {
    Warn "SkipBuild specified. Existing payload will be used."
  }

  if (-not (Test-Path $OutDir)) {
    Fail "deploy payload directory not found: $OutDir"
  }

  $required = @(
    (Join-Path $OutDir "static\index.html"),
    (Join-Path $OutDir "static\overlay.html"),
    (Join-Path $OutDir "static\sentiment.html"),
    (Join-Path $OutDir "static\digest.html"),
    (Join-Path $OutDir "data\digest\view_model_latest.json"),
    (Join-Path $OutDir "data\digest\health_latest.json"),
    (Join-Path $OutDir "data\world_politics\analysis\daily_summary_latest.json"),
    (Join-Path $OutDir "data\world_politics\analysis\sentiment_latest.json"),
    (Join-Path $OutDir "data\fx\fx_overlay_latest_jpythb.png"),
    (Join-Path $OutDir "data\fx\fx_decision_latest.json")
  )

  Info "=== 2) Validate deploy payload ==="
  $missing = @()
  foreach ($path in $required) {
    if (-not (Test-Path $path)) {
      $missing += $path
    }
  }

  if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "[FAIL] required deploy payload files are missing:" -ForegroundColor Red
    foreach ($m in $missing) {
      Write-Host "  - $m" -ForegroundColor Red
    }
    exit 1
  }
  Ok "Deploy payload validated"

  Info "=== 3) Run LABOS deploy ==="
  $argv = @(
    "-ExecutionPolicy", "Bypass",
    "-File", $deployScript,
    "-Profile", $Profile
  )
  if ($DryRun) { $argv += "-DryRun" }

  & powershell @argv
  if ($LASTEXITCODE -ne 0) {
    Fail "run_deploy_labos.ps1 failed (exit=$LASTEXITCODE)"
  }

  Ok "LABOS publish completed"
}
catch {
  Fail $_.Exception.Message
}
