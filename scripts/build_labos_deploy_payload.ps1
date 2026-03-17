# =========================================================
# GenesisPrediction v2
# build_labos_deploy_payload.ps1
# LABOS deploy payload builder (HARDENED - Phase2)
# =========================================================
# RULE:
# - payload は自己完結であること
# - 必須ファイル欠損時は即停止（WARN禁止）
# - root重要ファイルは必ず含める
# - manifest を生成する
# =========================================================

param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

# -----------------------------
# PATHS
# -----------------------------
$dist = Join-Path $Root "dist\labos_payload"
$manifestPath = Join-Path $dist "manifest.json"

Write-Host "========================================="
Write-Host "[build] LABOS PAYLOAD BUILD (HARDENED)"
Write-Host "========================================="
Write-Host "[build] ROOT: $Root"
Write-Host "[build] DIST: $dist"

# -----------------------------
# CLEAN DIST
# -----------------------------
if (Test-Path $dist) {
    Write-Host "[build] cleaning dist..."
    Remove-Item $dist -Recurse -Force
}
New-Item -ItemType Directory -Path $dist | Out-Null

# -----------------------------
# REQUIRED ROOT FILES
# -----------------------------
$requiredRootFiles = @(
    ".htaccess"
)

# -----------------------------
# REQUIRED DATA FILES（最低限）
# -----------------------------
$requiredDataFiles = @(
    "data\prediction\prediction_latest.json",
    "data\prediction\prediction_history_index.json"
)

# -----------------------------
# COPY: STATIC
# -----------------------------
$staticSrc = Join-Path $Root "app\static"
$staticDst = Join-Path $dist "static"

if (!(Test-Path $staticSrc)) {
    throw "[build][ERROR] missing static source: $staticSrc"
}

Write-Host "[build] static..."
Copy-Item $staticSrc -Destination $staticDst -Recurse -Force

# -----------------------------
# COPY: DATA
# -----------------------------
$dataSrc = Join-Path $Root "data"
$dataDst = Join-Path $dist "data"

if (!(Test-Path $dataSrc)) {
    throw "[build][ERROR] missing data source: $dataSrc"
}

Write-Host "[build] data..."
Copy-Item $dataSrc -Destination $dataDst -Recurse -Force

# -----------------------------
# COPY: ANALYSIS（公開対象）
# -----------------------------
$analysisSrc = Join-Path $Root "analysis"
$analysisDst = Join-Path $dist "analysis"

if (!(Test-Path $analysisSrc)) {
    throw "[build][ERROR] missing analysis source: $analysisSrc"
}

Write-Host "[build] analysis..."
Copy-Item $analysisSrc -Destination $analysisDst -Recurse -Force

# -----------------------------
# COPY: ROOT FILES（強制）
# -----------------------------
Write-Host "[build] root files..."

foreach ($file in $requiredRootFiles) {
    $src = Join-Path $Root $file
    if (!(Test-Path $src)) {
        throw "[build][ERROR] required root file missing: $file"
    }

    Copy-Item $src -Destination $dist -Force
    Write-Host "[build] copied root file: $file"
}

# -----------------------------
# PRECHECK: REQUIRED DATA FILES
# -----------------------------
Write-Host "[build] precheck required data..."

foreach ($relPath in $requiredDataFiles) {
    $fullPath = Join-Path $Root $relPath
    if (!(Test-Path $fullPath)) {
        throw "[build][ERROR] required data missing: $relPath"
    }
    Write-Host "[build] OK: $relPath"
}

# -----------------------------
# MANIFEST GENERATION
# -----------------------------
Write-Host "[build] generating manifest..."

$files = Get-ChildItem -Path $dist -Recurse -File

$manifest = @()

foreach ($f in $files) {
    $relative = $f.FullName.Replace($dist + "\", "")
    $manifest += @{
        path = $relative
        size = $f.Length
        last_write = $f.LastWriteTimeUtc.ToString("o")
    }
}

$manifestObject = @{
    build_time_utc = (Get-Date).ToUniversalTime().ToString("o")
    file_count = $manifest.Count
    files = $manifest
}

$manifestObject | ConvertTo-Json -Depth 5 | Out-File -Encoding UTF8 $manifestPath

Write-Host "[build] manifest created: $manifestPath"

# -----------------------------
# SUMMARY
# -----------------------------
Write-Host "-----------------------------------------"
Write-Host "[build] FILE COUNT: $($manifest.Count)"
Write-Host "[build] SUCCESS"
Write-Host "-----------------------------------------"