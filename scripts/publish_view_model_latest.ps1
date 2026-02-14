# scripts/publish_view_model_latest.ps1
# Publish WORLD view_model_latest.json for localhost-served analysis and dist package.
#
# Localhost serves /analysis from: data/world_politics/analysis
# So WORLD source MUST be taken from data/world_politics/analysis only.
#
# Digest view model is published to dist only under a different name to avoid conflicts.
#
# Safety:
# - Never overwrite world with digest
# - Skip copy if src == dst

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
  try { $dstFull = (Resolve-Path $dst).Path } catch { }

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

function Pick-WorldSource([string]$root) {
  $analysisDir = Join-Path $root "data\world_politics\analysis"

  # Prefer view_model_latest.json if it's present and non-trivial
  $vmLatest = Join-Path $analysisDir "view_model_latest.json"
  if (Test-Path $vmLatest -PathType Leaf) {
    $fi = Get-Item $vmLatest
    # Must not be empty model
    if ($fi.Length -ge 3000) { return $vmLatest }
  }

  # Otherwise, pick newest big view_model*.json in the same folder (dated ones)
  $cand = Get-ChildItem -Path $analysisDir -File -Filter "view_model*.json" -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -ge 3000 } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

  if ($cand) { return $cand.FullName }

  return $null
}

function Pick-OptionalDigest([string]$root) {
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

$srcWorld = Pick-WorldSource $root
if (-not $srcWorld) {
  Write-Host "[ERR] WORLD view_model not found in data/world_politics/analysis (>=3000 bytes)."
  Write-Host "Hint: generate it first (run daily pipeline that builds view_model), then retry."
  exit 2
}

Write-Host "[INFO] Publishing WORLD view_model_latest.json (for Sentiment + GUI)..."
Write-Host "       SRC(world): $srcWorld"
Copy-WithReport $srcWorld (Join-Path $servedAnalysisDir "view_model_latest.json")
Copy-WithReport $srcWorld (Join-Path $distAnalysisDir   "view_model_latest.json")

$srcDigest = Pick-OptionalDigest $root
if ($srcDigest) {
  Write-Host "[INFO] Publishing DIGEST view_model as view_model_digest_latest.json (dist only)..."
  Write-Host "       SRC(digest): $srcDigest"
  Copy-WithReport $srcDigest (Join-Path $distAnalysisDir "view_model_digest_latest.json")
} else {
  Write-Host "[WARN] digest view_model not found (skipped)."
}

Write-Host "[DONE] publish_view_model_latest completed."
