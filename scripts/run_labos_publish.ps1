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

  Info "=== 3) Freshness gate ==="

  function Get-JsonTopLevelField {
    param(
      [Parameter(Mandatory=$true)]
      [string]$JsonPath,

      [Parameter(Mandatory=$true)]
      [string]$Field
    )

    if (-not (Test-Path $JsonPath)) {
      Fail "json field source missing: $JsonPath"
    }

    $pythonSource = @'
import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    print("usage: get_json_field.py <path> <field>", file=sys.stderr)
    sys.exit(2)

path = Path(sys.argv[1])
field = sys.argv[2]

with path.open("r", encoding="utf-8-sig") as f:
    obj = json.load(f)

if not isinstance(obj, dict):
    print("top-level JSON value is not an object", file=sys.stderr)
    sys.exit(3)

value = obj.get(field, "")

if value is None:
    value = ""

if isinstance(value, (dict, list)):
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
else:
    print(str(value))
'@

    $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("gp_json_field_{0}.py" -f ([Guid]::NewGuid().ToString("N")))

    try {
      Set-Content -Path $tempScript -Value $pythonSource -Encoding UTF8
      $output = & python $tempScript $JsonPath $Field
      $exitCode = $LASTEXITCODE

      if ($exitCode -ne 0) {
        Fail "failed to read json field: $JsonPath [$Field]"
      }

      return (($output -join "`n").Trim())
    }
    finally {
      if (Test-Path $tempScript) {
        Remove-Item -Force $tempScript
      }
    }
  }

  $expectedAsOf = Get-JsonTopLevelField `
    -JsonPath (Join-Path $repoRoot "analysis\global_status_latest.json") `
    -Field "as_of"

  if ([string]::IsNullOrWhiteSpace($expectedAsOf)) {
    Fail "expected as_of is empty: analysis\global_status_latest.json"
  }

  $checks = @(
    @{ Path = (Join-Path $OutDir "analysis\global_status_latest.json"); Field = "as_of" },
    @{ Path = (Join-Path $OutDir "analysis\prediction\prediction_latest.json"); Field = "as_of" },
    @{ Path = (Join-Path $OutDir "analysis\explanation\prediction_explanation_latest.json"); Field = "as_of" },
    @{ Path = (Join-Path $OutDir "data\world_politics\analysis\latest.json"); Field = "date" }
  )

  foreach ($check in $checks) {
    if (-not (Test-Path $check.Path)) {
      Fail "freshness check file missing: $($check.Path)"
    }

    $value = Get-JsonTopLevelField `
      -JsonPath $check.Path `
      -Field $check.Field

    if ($value -ne $expectedAsOf) {
      Fail "freshness mismatch: $($check.Path) expected=$expectedAsOf actual=$value"
    }
  }
  Ok "Freshness gate passed"

  Info "=== 4) Run LABOS deploy ==="
  $argv = @(
    "-ExecutionPolicy", "Bypass",
    "-File", $deployScript
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
