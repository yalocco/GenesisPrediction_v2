# scripts/fx_usdthb_manual.ps1
# Manual USDTHB seed/append (no file editing by hand)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/fx_usdthb_manual.ps1 -rate 35.80
#   powershell -ExecutionPolicy Bypass -File scripts/fx_usdthb_manual.ps1 -date 2026-02-10 -rate 35.80
#
param(
  [string]$date = (Get-Date -Format "yyyy-MM-dd"),
  [Parameter(Mandatory=$true)][double]$rate
)

$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path "$PSScriptRoot\.."
$SRC  = Join-Path $ROOT "data\fx\usdthb_source.csv"

function Ensure-Dir([string]$p) { if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null } }

# validate date
try { [void][datetime]::ParseExact($date, "yyyy-MM-dd", $null) } catch { throw "Invalid -date (expected yyyy-MM-dd): $date" }

Ensure-Dir (Split-Path $SRC -Parent)

# create header if not exist
if (-not (Test-Path $SRC)) {
  "date,rate" | Out-File -FilePath $SRC -Encoding utf8
}

# prevent duplicate date (keep last line per date policy by rewriting file)
$lines = Get-Content -Path $SRC -ErrorAction Stop
$header = $lines[0]
$body = @()
if ($lines.Count -gt 1) { $body = $lines[1..($lines.Count-1)] }

# remove existing line for the same date
$body = $body | Where-Object { $_ -notmatch "^$date," }

# append new line
$body += ("{0},{1}" -f $date, $rate)

# write back (header + body)
@($header) + $body | Out-File -FilePath $SRC -Encoding utf8

Write-Host "[OK] updated source: $SRC"
Write-Host "     last: $date,$rate"

# materialize usdthb.csv from source
Push-Location $ROOT
try {
  & python "scripts\fx_materialize_rates.py" --pair usdthb
  if ($LASTEXITCODE -ne 0) { throw "fx_materialize_rates.py failed exit=$LASTEXITCODE" }
} finally {
  Pop-Location
}

Write-Host "[OK] materialized usdthb.csv"
