# =========================================================
# GenesisPrediction v2
# build_labos_deploy_payload.ps1
# LABOS Deploy Payload Builder
# (FULL PAYLOAD / analysis+data / target-safe deploy support)
# =========================================================

param(
    [string]$RepoRoot = ".",
    [string]$OutDir = "dist/labos_deploy"
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[build_labos_deploy_payload] $msg"
}

$root = (Resolve-Path $RepoRoot).Path
$out  = Join-Path $root $OutDir

Log "ROOT : $root"
Log "OUT  : $out"

if (Test-Path $out) {
    Remove-Item -Recurse -Force $out
}
New-Item -ItemType Directory -Path $out | Out-Null

$rootFiles = @(
    ".htaccess"
)

foreach ($name in $rootFiles) {
    $src = Join-Path $root $name
    if (!(Test-Path $src)) {
        throw "Missing required root file: $src"
    }
    Copy-Item -Force $src $out
    Log "Copy root file: $name"
}

$staticSrc = Join-Path $root "app/static"
$staticDst = Join-Path $out  "static"

if (!(Test-Path $staticSrc)) {
    throw "app/static not found: $staticSrc"
}

Log "Copy static..."
Copy-Item -Recurse -Force $staticSrc $staticDst

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
    if (!(Test-Path $src)) {
        throw "Missing required root html: $src"
    }
    Copy-Item -Force $src (Join-Path $out $name)
    Log "Copy root html: $name"
}

$dataSrc = Join-Path $root "data"
$dataDst = Join-Path $out  "data"

if (!(Test-Path $dataSrc)) {
    throw "data directory not found: $dataSrc"
}

Log "Copy full data directory..."
Copy-Item -Recurse -Force $dataSrc $dataDst

$analysisSrc = Join-Path $root "analysis"
$analysisDst = Join-Path $out  "analysis"

if (!(Test-Path $analysisSrc)) {
    throw "analysis directory not found: $analysisSrc"
}

Log "Copy full analysis directory..."
Copy-Item -Recurse -Force $analysisSrc $analysisDst

$analysisPredictionSrc = Join-Path $analysisDst "prediction"
$dataPredictionDst     = Join-Path $dataDst "prediction"

if (!(Test-Path $analysisPredictionSrc)) {
    throw "analysis/prediction not found in payload: $analysisPredictionSrc"
}

Log "Copy prediction compatibility snapshot (analysis -> data/prediction)..."
if (Test-Path $dataPredictionDst) {
    Remove-Item -Recurse -Force $dataPredictionDst
}
New-Item -ItemType Directory -Path $dataPredictionDst -Force | Out-Null
Copy-Item -Recurse -Force "$analysisPredictionSrc\*" $dataPredictionDst

$analysisExplanationSrc = Join-Path $analysisDst "explanation"
$dataExplanationDst     = Join-Path $dataDst "explanation"

if (!(Test-Path $analysisExplanationSrc)) {
    throw "analysis/explanation not found in payload: $analysisExplanationSrc"
}

Log "Copy explanation compatibility snapshot (analysis -> data/explanation)..."
if (Test-Path $dataExplanationDst) {
    Remove-Item -Recurse -Force $dataExplanationDst
}
New-Item -ItemType Directory -Path $dataExplanationDst -Force | Out-Null
Copy-Item -Recurse -Force "$analysisExplanationSrc\*" $dataExplanationDst

$requiredPrediction = @(
    "trend_latest.json",
    "signal_latest.json",
    "early_warning_latest.json",
    "scenario_latest.json",
    "prediction_latest.json",
    "prediction_history_index.json"
)

foreach ($f in $requiredPrediction) {
    $p1 = Join-Path $analysisPredictionSrc $f
    $p2 = Join-Path $dataPredictionDst $f
    if (!(Test-Path $p1)) {
        throw "Missing required prediction file in analysis payload: $p1"
    }
    if (!(Test-Path $p2)) {
        throw "Missing required prediction file in data compatibility payload: $p2"
    }
}

$requiredExplanation = @(
    "prediction_explanation_latest.json",
    "scenario_explanation_latest.json"
)

foreach ($f in $requiredExplanation) {
    $p1 = Join-Path $analysisExplanationSrc $f
    $p2 = Join-Path $dataExplanationDst $f
    if (!(Test-Path $p1)) {
        throw "Missing required explanation file in analysis payload: $p1"
    }
    if (!(Test-Path $p2)) {
        throw "Missing required explanation file in data compatibility payload: $p2"
    }
}

Log "All required prediction files OK"
Log "All required explanation files OK"

$historyDir = Join-Path $analysisPredictionSrc "history"
if (!(Test-Path $historyDir)) {
    Log "[WARN] analysis history directory not found"
}
else {
    $count = (Get-ChildItem $historyDir -Recurse -Filter prediction.json | Measure-Object).Count
    Log "Analysis history snapshots: $count"
}

$manifest = @{
    built_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    out_dir = $out.ToString()
    includes = @(
        ".htaccess",
        "root html",
        "static/",
        "data/",
        "analysis/",
        "data/prediction/ (compatibility copy from analysis/prediction)",
        "data/explanation/ (compatibility copy from analysis/explanation)"
    )
    deploy_scope = "target hierarchy only: labos.soma-samui.com"
}

$manifestPath = Join-Path $out "manifest.json"
$manifest | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $manifestPath
Log "Manifest written: $manifestPath"

Log "Payload build complete"
Log "OUTPUT: $out"
