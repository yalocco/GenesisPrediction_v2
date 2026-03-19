# =========================================================
# GenesisPrediction v2
# build_labos_deploy_payload.ps1
# LABOS Deploy Payload Builder (Phase4 / Explanation-ready)
# =========================================================

param(
    [string]$RepoRoot = ".",
    [string]$OutDir = "dist/labos_deploy"
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[build_labos_deploy_payload] $msg"
}

# ---------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------
$root = Resolve-Path $RepoRoot
$out  = Join-Path $root $OutDir

Log "ROOT : $root"
Log "OUT  : $out"

# Clean
if (Test-Path $out) {
    Remove-Item -Recurse -Force $out
}
New-Item -ItemType Directory -Path $out | Out-Null

# ---------------------------------------------------------
# 0. Root files for public deploy
# ---------------------------------------------------------
$rootFiles = @(
    ".htaccess"
)

foreach ($name in $rootFiles) {
    $src = Join-Path $root $name
    if (Test-Path $src) {
        Copy-Item -Force $src $out
        Log "Copy root file: $name"
    }
}

# ---------------------------------------------------------
# 1. Copy static UI
# ---------------------------------------------------------
$staticSrc = Join-Path $root "app/static"
$staticDst = Join-Path $out  "static"

if (!(Test-Path $staticSrc)) {
    throw "app/static not found: $staticSrc"
}

Log "Copy static..."
Copy-Item -Recurse -Force $staticSrc $staticDst

# publish root html entrypoints too
$rootHtml = @(
    "index.html",
    "overlay.html",
    "sentiment.html",
    "digest.html",
    "prediction.html",
    "prediction_history.html"
)

foreach ($name in $rootHtml) {
    $src = Join-Path $staticSrc $name
    if (Test-Path $src) {
        Copy-Item -Force $src (Join-Path $out $name)
        Log "Copy root html: $name"
    }
}

# ---------------------------------------------------------
# 2. Prepare data / analysis directories
# ---------------------------------------------------------
$dataDst = Join-Path $out "data"
$analysisDst = Join-Path $out "analysis"

New-Item -ItemType Directory -Path $dataDst -Force | Out-Null
New-Item -ItemType Directory -Path $analysisDst -Force | Out-Null

# ---------------------------------------------------------
# 3. Copy existing data directory
# ---------------------------------------------------------
$dataSrc = Join-Path $root "data"
if (Test-Path $dataSrc) {
    Log "Copy data..."
    Copy-Item -Recurse -Force "$dataSrc\*" $dataDst
}

# ---------------------------------------------------------
# 4. Copy prediction artifacts from analysis -> data/prediction
# ---------------------------------------------------------
$analysisPrediction = Join-Path $root "analysis\prediction"
$dataPredictionDst  = Join-Path $dataDst "prediction"

if (!(Test-Path $analysisPrediction)) {
    throw "analysis/prediction not found: $analysisPrediction"
}

Log "Copy prediction (analysis -> data)..."
New-Item -ItemType Directory -Path $dataPredictionDst -Force | Out-Null
Copy-Item -Recurse -Force "$analysisPrediction\*" $dataPredictionDst

# ---------------------------------------------------------
# 5. Copy explanation artifacts from analysis -> analysis/explanation
#    and -> data/explanation for backward compatibility
# ---------------------------------------------------------
$analysisExplanationSrc = Join-Path $root "analysis\explanation"
$analysisExplanationDst = Join-Path $analysisDst "explanation"
$dataExplanationDst     = Join-Path $dataDst "explanation"

if (!(Test-Path $analysisExplanationSrc)) {
    throw "analysis/explanation not found: $analysisExplanationSrc"
}

Log "Copy explanation (analysis -> analysis / data)..."
New-Item -ItemType Directory -Path $analysisExplanationDst -Force | Out-Null
New-Item -ItemType Directory -Path $dataExplanationDst -Force | Out-Null

Copy-Item -Recurse -Force "$analysisExplanationSrc\*" $analysisExplanationDst
Copy-Item -Recurse -Force "$analysisExplanationSrc\*" $dataExplanationDst

# ---------------------------------------------------------
# 6. Copy FX analysis required by UI
# ---------------------------------------------------------
$analysisFxSrc = Join-Path $root "analysis\fx"
$analysisFxDst = Join-Path $analysisDst "fx"

if (Test-Path $analysisFxSrc) {
    Log "Copy fx analysis..."
    New-Item -ItemType Directory -Path $analysisFxDst -Force | Out-Null
    Copy-Item -Recurse -Force "$analysisFxSrc\*" $analysisFxDst
}

# ---------------------------------------------------------
# 7. Required files check
# ---------------------------------------------------------
$requiredPrediction = @(
    "trend_latest.json",
    "signal_latest.json",
    "early_warning_latest.json",
    "scenario_latest.json",
    "prediction_latest.json",
    "prediction_history_index.json"
)

foreach ($f in $requiredPrediction) {
    $p = Join-Path $dataPredictionDst $f
    if (!(Test-Path $p)) {
        throw "Missing required prediction file: $p"
    }
}

$requiredExplanation = @(
    "prediction_explanation_latest.json",
    "scenario_explanation_latest.json"
)

foreach ($f in $requiredExplanation) {
    $p1 = Join-Path $analysisExplanationDst $f
    $p2 = Join-Path $dataExplanationDst $f
    if (!(Test-Path $p1)) {
        throw "Missing required explanation file: $p1"
    }
    if (!(Test-Path $p2)) {
        throw "Missing required explanation compatibility file: $p2"
    }
}

Log "All required prediction files OK"
Log "All required explanation files OK"

# ---------------------------------------------------------
# 8. History check
# ---------------------------------------------------------
$historyDir = Join-Path $dataPredictionDst "history"
if (!(Test-Path $historyDir)) {
    Log "[WARN] history directory not found"
} else {
    $count = (Get-ChildItem $historyDir -Recurse -Filter prediction.json | Measure-Object).Count
    Log "History snapshots: $count"
}

# ---------------------------------------------------------
# 9. Manifest
# ---------------------------------------------------------
$manifest = @{
    built_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    out_dir = $out.ToString()
    includes = @(
        ".htaccess",
        "root html",
        "static/",
        "data/",
        "data/prediction/",
        "data/explanation/",
        "analysis/explanation/",
        "analysis/fx/"
    )
}

$manifestPath = Join-Path $out "manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manifestPath
Log "Manifest written: $manifestPath"

# ---------------------------------------------------------
# 10. Summary
# ---------------------------------------------------------
Log "Payload build complete"
Log "OUTPUT: $out"
