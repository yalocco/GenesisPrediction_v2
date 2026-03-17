# GenesisPrediction v2
# build_labos_deploy_payload.ps1
# LABOS deploy payload builder
# RULE: rootファイルも必ず含める（.htaccessなど）

param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

$dist = Join-Path $Root "dist\labos_payload"
if (Test-Path $dist) {
    Remove-Item $dist -Recurse -Force
}
New-Item -ItemType Directory -Path $dist | Out-Null

Write-Host "[build] ROOT: $Root"
Write-Host "[build] DIST: $dist"

# -----------------------------
# 1. static
# -----------------------------
$staticSrc = Join-Path $Root "app\static"
$staticDst = Join-Path $dist "static"

Write-Host "[build] static..."
Copy-Item $staticSrc -Destination $staticDst -Recurse -Force

# -----------------------------
# 2. data
# -----------------------------
$dataSrc = Join-Path $Root "data"
$dataDst = Join-Path $dist "data"

Write-Host "[build] data..."
Copy-Item $dataSrc -Destination $dataDst -Recurse -Force

# -----------------------------
# 3. analysis（公開用のみ）
# -----------------------------
$analysisSrc = Join-Path $Root "analysis"
$analysisDst = Join-Path $dist "analysis"

Write-Host "[build] analysis..."
Copy-Item $analysisSrc -Destination $analysisDst -Recurse -Force

# -----------------------------
# 4. ROOT FILES（重要）
# -----------------------------
Write-Host "[build] root files..."

$rootFiles = @(
    ".htaccess"
)

foreach ($file in $rootFiles) {
    $src = Join-Path $Root $file
    if (Test-Path $src) {
        Copy-Item $src -Destination $dist -Force
        Write-Host "[build] copied root file: $file"
    } else {
        Write-Host "[build][WARN] missing root file: $file"
    }
}

# -----------------------------
# 完了
# -----------------------------
Write-Host "[build] DONE"