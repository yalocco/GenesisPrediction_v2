# scripts/publish_view_model_latest.ps1
# Publish "WORLD" view_model_latest.json for GUI/Sentiment without breaking join.
#
# Facts from your environment:
# - localhost (/analysis/...) is served from: data/world_politics/analysis
# - digest view_model_latest.json is small (~1-2KB) and must NOT overwrite world.
#
# This script:
# 1) Finds the newest "WORLD-like" view_model*.json (size >= 3000 AND contains "world_politics")
# 2) Publishes it to:
#    - data/world_politics/analysis/view_model_latest.json   (served)
#    - dist/labos_deploy/analysis/view_model_latest.json     (deploy package)
# 3) Publishes digest view model (optional) to dist only under:
#    - dist/labos_deploy/analysis/view_model_digest_latest.json
#
# Safety:
# - Never copies digest into data/world_politics/analysis
# - Skips copy if src == dst (prevents "overwrite itself" error)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $here = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $here "..")).Path
}

function Ensure-Dir([string]$dirPath) {
  if (!(Test-Path $dirPath -PathType Container)) {
    New-Item -ItemType Directory -Path $dirPath | Out-Null
  }
}

function Copy-WithReport([string]$src, [string]$dst) {
  $srcFull = (Resolve-Path $src).Path
  $dstFull = $dst
  try { $dstFull = (Resolve-Path $dst).Path } catch { } # dst may not exist yet

  if ($srcFull -eq $dstFull) {
    $s = Get-Item $srcFull
    Write-Host "[SKIP] src == dst (no-op)"
    Write-Host "      PATH: $($s.FullName) ($($s.Length) bytes, $($s.LastWriteTime))"
    return
  }

  $dstDir = Split-Path -Parent $dst
  Ensure-Dir $dstDir

  Copy-Item -Force $srcFull $dst

  $s = Get-Item $srcFull
  $d = Get-Item $dst

  Write-Host "[OK] copied"
  Write-Host "     SRC: $($s.FullName)  ($($s.Length) bytes, $($s.LastWriteTime))"
  Write-Host "     DST: $($d.FullName)  ($($d.Length) bytes, $($d.LastWriteTime))"
}

function Is-WorldViewModel([string]$path) {
  try {
    $fi = Get-Item $path
    if ($fi.Length -lt 3000) { return $false } # digest is small
    # quick signature checks (fast, no full JSON parse)
    $hit1 = Select-String -Path $path -Pattern '"sections"' -SimpleMatch -Quiet
    if (-not $hit1) { return $false }
    $hit2 = Select-String -Path $path -Pattern 'world_politics' -SimpleMatch -Quiet
    if (-not $hit2) { return $false }
    return $true
  } catch {
    return $false
  }
}

function Find-WorldViewModel([string]$root) {
  # Search broadly, but exclude digest folder to prevent accidental selection.
  $candidates = Get-ChildItem -Path $root -Recurse -File -Filter "view_model*.json" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\data\\digest\\" }

  $world = $candidates |
    Where-Object { Is-WorldViewModel $_.FullName } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

  if ($null -eq $world) { return $null }
  return $world.FullName
}

function Find-OptionalDigest([string]$root) {
  $candidates = @(
    (Join-Path $root "data\digest\view\view_model_latest.json"),
    (Join-Path $root "data\digest\view_model_latest.json")
  )
  foreach ($p in $candidates) {
    if (Test-Path $p -PathType Leaf) { return $p }
  }
  return $null
}

# ---------------------------
# Main
# ---------------------------
$root = Resolve-RepoRoot

$servedAnalysisDir = Join-Path $root "data\world_politics\analysis"
$distAnalysisDir   = Join-Path $root "dist\labos_deploy\analysis"

$srcWorld = Find-WorldViewModel $root
if (-not $srcWorld) {
  Write-Host "[ERR] WORLD view_model*.json not found (size>=3000 + contains 'world_politics')."
  Write-Host "Hint: run the pipeline that generates world view_model, then retry."
  exit 2
}

Write-Host "[INFO] Publishing WORLD view_model_latest.json (for Sentiment + GUI)..."
Write-Host "       SRC(world): $srcWorld"
Copy-WithReport $srcWorld (Join-Path $servedAnalysisDir "view_model_latest.json")
Copy-WithReport $srcWorld (Join-Path $distAnalysisDir   "view_model_latest.json")

$srcDigest = Find-OptionalDigest $root
if ($srcDigest) {
  Write-Host "[INFO] Publishing DIGEST view_model as view_model_digest_latest.json (dist only)..."
  Write-Host "       SRC(digest): $srcDigest"
  Copy-WithReport $srcDigest (Join-Path $distAnalysisDir "view_model_digest_latest.json")
} else {
  Write-Host "[WARN] digest view_model not found (skipped)."
}

Write-Host "[DONE] publish_view_model_latest completed."
