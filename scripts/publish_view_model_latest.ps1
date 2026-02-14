# scripts/publish_view_model_latest.ps1
# Publish latest view_model_latest.json to the served /analysis folder(s)
# Safe: copy only, no deletion. Creates folders if missing.

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  # Assume this script is under <repo>\scripts\
  $here = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $here "..")).Path
}

function Pick-FirstExistingFile([string[]]$candidates) {
  foreach ($p in $candidates) {
    if (Test-Path $p -PathType Leaf) { return $p }
  }
  return $null
}

function Ensure-Dir([string]$dirPath) {
  if (!(Test-Path $dirPath -PathType Container)) {
    New-Item -ItemType Directory -Path $dirPath | Out-Null
  }
}

function Copy-WithReport([string]$src, [string]$dst) {
  $dstDir = Split-Path -Parent $dst
  Ensure-Dir $dstDir

  Copy-Item -Force $src $dst

  $s = Get-Item $src
  $d = Get-Item $dst

  Write-Host "[OK] copied"
  Write-Host "     SRC: $($s.FullName)  ($($s.Length) bytes, $($s.LastWriteTime))"
  Write-Host "     DST: $($d.FullName)  ($($d.Length) bytes, $($d.LastWriteTime))"
}

# ---------------------------
# Main
# ---------------------------
$root = Resolve-RepoRoot

# Source priority:
# 1) data/digest/view/view_model_latest.json (new pipeline)
# 2) data/digest/view_model_latest.json
# (If both exist, the first one is used)
$srcCandidates = @(
  (Join-Path $root "data\digest\view\view_model_latest.json"),
  (Join-Path $root "data\digest\view_model_latest.json")
)

$src = Pick-FirstExistingFile $srcCandidates
if (-not $src) {
  Write-Host "[ERR] source view_model_latest.json not found in digest outputs."
  Write-Host "Tried:"
  $srcCandidates | ForEach-Object { Write-Host " - $_" }
  exit 1
}

# Targets:
# - dist/labos_deploy/analysis (served on localhost in your current setup)
# - data/world_politics/analysis (legacy location; keep consistent)
$targets = @(
  (Join-Path $root "dist\labos_deploy\analysis\view_model_latest.json"),
  (Join-Path $root "data\world_politics\analysis\view_model_latest.json")
)

Write-Host "[INFO] Publishing view_model_latest.json..."
Write-Host "       Using source: $src"

foreach ($t in $targets) {
  Copy-WithReport $src $t
}

Write-Host "[DONE] publish_view_model_latest completed."
