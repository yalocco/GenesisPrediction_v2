# scripts/run_daily_with_publish.ps1
# Wrapper: run daily pipeline, then publish view_model_latest to served /analysis.
# Safe: does not modify existing scripts/run_daily.ps1.

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $here = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $here "..")).Path
}

$root = Resolve-RepoRoot

$runDaily = Join-Path $root "scripts\run_daily.ps1"
$publish  = Join-Path $root "scripts\publish_view_model_latest.ps1"

if (!(Test-Path $runDaily -PathType Leaf)) {
  Write-Host "[ERR] not found: $runDaily"
  exit 1
}
if (!(Test-Path $publish -PathType Leaf)) {
  Write-Host "[ERR] not found: $publish"
  exit 1
}

Write-Host "[INFO] 1) run_daily"
& powershell -ExecutionPolicy Bypass -File $runDaily
$code = $LASTEXITCODE

if ($code -ne 0) {
  Write-Host "[ERR] run_daily failed (exit=$code). publish is skipped."
  exit $code
}

Write-Host "[INFO] 2) publish view_model_latest"
& powershell -ExecutionPolicy Bypass -File $publish
$code2 = $LASTEXITCODE

if ($code2 -ne 0) {
  Write-Host "[ERR] publish_view_model_latest failed (exit=$code2)."
  exit $code2
}

Write-Host "[OK] run_daily + publish completed."
exit 0
