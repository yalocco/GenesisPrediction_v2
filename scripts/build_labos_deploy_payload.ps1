param(
    [string]$Root = (Resolve-Path ".").Path
)

Write-Host "LABOS Deploy Payload Builder"
Write-Host "ROOT : $Root"

$dist = Join-Path $Root "dist\labos_payload"

if (Test-Path $dist) {
    Remove-Item $dist -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $dist | Out-Null

function Ensure-Dir {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Copy-Tree {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (Test-Path $Source) {
        Write-Host "[COPY] $Source -> $Destination"
        Ensure-Dir -Path $Destination
        Copy-Item "$Source\*" $Destination -Recurse -Force
    }
    else {
        Write-Host "[SKIP] missing directory: $Source"
    }
}

function Copy-FileSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (Test-Path $Source) {
        $parent = Split-Path $Destination -Parent
        Ensure-Dir -Path $parent
        Write-Host "[COPY] $Source -> $Destination"
        Copy-Item $Source $Destination -Force
    }
    else {
        Write-Host "[SKIP] missing file: $Source"
    }
}

# --------------------------------------------------
# STATIC UI
# --------------------------------------------------

Copy-Tree -Source "$Root\app\static" -Destination "$dist\static"

# --------------------------------------------------
# ANALYSIS JSON
# Keep full analysis mirror for internal/debug use
# --------------------------------------------------

Copy-Tree -Source "$Root\analysis" -Destination "$dist\analysis"

# --------------------------------------------------
# DATA (needed runtime JSON)
# --------------------------------------------------

Copy-Tree -Source "$Root\data\world_politics\analysis" -Destination "$dist\data\world_politics\analysis"

# --------------------------------------------------
# FX OVERLAY IMAGES / JSON
# --------------------------------------------------

Copy-Tree -Source "$Root\analysis\fx" -Destination "$dist\analysis\fx"
Copy-Tree -Source "$Root\data\world_politics\analysis\fx" -Destination "$dist\data\world_politics\analysis\fx"
Copy-Tree -Source "$Root\data\fx" -Destination "$dist\data\fx"

# --------------------------------------------------
# PREDICTION PUBLISH CONTRACT
# analysis/prediction -> dist/data/prediction
# Publish is copy-only. No recomputation.
# --------------------------------------------------

$predictionSrc = "$Root\analysis\prediction"
$predictionDst = "$dist\data\prediction"

Ensure-Dir -Path $predictionDst

Copy-FileSafe `
    -Source "$predictionSrc\prediction_latest.json" `
    -Destination "$predictionDst\prediction_latest.json"

Copy-FileSafe `
    -Source "$predictionSrc\prediction_history_index.json" `
    -Destination "$predictionDst\prediction_history_index.json"

Copy-Tree `
    -Source "$predictionSrc\history" `
    -Destination "$predictionDst\history"

# --------------------------------------------------
# OPTIONAL: keep internal prediction mirror in dist/analysis
# already covered by full analysis copy above
# --------------------------------------------------

Write-Host ""
Write-Host "Payload ready:"
Write-Host $dist

Write-Host ""
Write-Host "[VERIFY] Prediction publish targets"
if (Test-Path "$predictionDst\prediction_latest.json") {
    Write-Host "  OK  data\prediction\prediction_latest.json"
}
else {
    Write-Host "  MISS data\prediction\prediction_latest.json"
}

if (Test-Path "$predictionDst\prediction_history_index.json") {
    Write-Host "  OK  data\prediction\prediction_history_index.json"
}
else {
    Write-Host "  MISS data\prediction\prediction_history_index.json"
}

if (Test-Path "$predictionDst\history") {
    Write-Host "  OK  data\prediction\history\"
}
else {
    Write-Host "  MISS data\prediction\history\"
}