# run_daily.ps1 (repo root)
# Wrapper: call scripts/run_daily.ps1 with the same args

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $here "scripts\run_daily.ps1"

if (!(Test-Path $target)) {
  throw "Missing: $target"
}

& $target @args
