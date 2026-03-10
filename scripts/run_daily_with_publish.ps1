param(
    [string]$Date = "",
    [string]$Root = "",
    [switch]$AllowDirtyRepo,
    [switch]$SkipAnalyzer,
    [switch]$SkipSentiment,
    [switch]$SkipDigest,
    [switch]$SkipPrediction,
    [switch]$ContinueOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    Write-Host "[$ts] $Message"
}

function Resolve-RepoRoot {
    param([string]$ExplicitRoot)

    if (-not [string]::IsNullOrWhiteSpace($ExplicitRoot)) {
        return (Resolve-Path $ExplicitRoot).Path
    }

    if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    }

    if ($MyInvocation.MyCommand.Path) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        return (Resolve-Path (Join-Path $scriptDir "..")).Path
    }

    return (Get-Location).Path
}

function Ensure-Dir {
    param([string]$PathToEnsure)
    if (-not (Test-Path -LiteralPath $PathToEnsure)) {
        New-Item -ItemType Directory -Path $PathToEnsure -Force | Out-Null
    }
}

function Copy-IfExists {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )
    if (Test-Path -LiteralPath $SourcePath) {
        $destDir = Split-Path -Parent $DestinationPath
        if (-not [string]::IsNullOrWhiteSpace($destDir)) {
            Ensure-Dir -PathToEnsure $destDir
        }
        Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
        Write-Log "[OK] alias: $DestinationPath"
        return $true
    }
    return $false
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Log "=== $Name ==="
    try {
        & $Action
    }
    catch {
        if ($ContinueOnError) {
            Write-Warning "$Name failed: $($_.Exception.Message)"
        }
        else {
            throw
        }
    }
}

function Invoke-PythonScript {
    param(
        [string]$PythonExe,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Log "[SKIP] missing script: $ScriptPath"
        return
    }

    $argText = if ($Arguments.Count -gt 0) { $Arguments -join " " } else { "" }
    Write-Host "CMD: $PythonExe $ScriptPath $argText"
    & $PythonExe $ScriptPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$([System.IO.Path]::GetFileName($ScriptPath)) failed with exit code $LASTEXITCODE."
    }
}

$Root = Resolve-RepoRoot -ExplicitRoot $Root
if ([string]::IsNullOrWhiteSpace($Date)) {
    $Date = Get-Date -Format "yyyy-MM-dd"
}

$python = Join-Path $Root ".venv\Scripts\python.exe"
$scriptsDir = Join-Path $Root "scripts"
$dataDir = Join-Path $Root "data\world_politics"
$dataAnalysisDir = Join-Path $dataDir "analysis"
$analysisDir = Join-Path $Root "analysis"
$predictionDir = Join-Path $analysisDir "prediction"
$predictionHistoryDir = Join-Path $analysisDir "prediction_history"

Ensure-Dir -PathToEnsure $analysisDir
Ensure-Dir -PathToEnsure $predictionDir
Ensure-Dir -PathToEnsure $predictionHistoryDir

Write-Host "GenesisPrediction v2 - run_daily_with_publish"
Write-Host "ROOT : $Root"
Write-Host "DATE : $Date"
Write-Host ("GUARD: " + ($(if ($AllowDirtyRepo) { "OFF" } else { "ON" })))

Push-Location $Root
try {
    if (-not $AllowDirtyRepo) {
        $gitStatus = git status --porcelain 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($gitStatus | Out-String))) {
            throw "Working tree is not clean. Commit/stash changes or rerun with -AllowDirtyRepo."
        }
    }
    else {
        Write-Log "Dirty repo allowed by flag."
    }

    Invoke-Step -Name "1) Analyzer (docker compose run --rm analyzer)" -Action {
        if ($SkipAnalyzer) {
            Write-Log "[SKIP] analyzer skipped by flag."
            return
        }

        Write-Host "CMD: docker compose run --rm analyzer"
        docker compose run --rm analyzer
        if ($LASTEXITCODE -ne 0) {
            throw "Analyzer failed with exit code $LASTEXITCODE."
        }

        $latestJson = Join-Path $dataAnalysisDir "latest.json"
        $summaryJson = Join-Path $dataAnalysisDir "summary.json"

        $dailyNewsLatest = Join-Path $dataAnalysisDir "daily_news_latest.json"
        $dailyNewsDated  = Join-Path $dataAnalysisDir ("daily_news_{0}.json" -f $Date)

        $dailySummaryLatest = Join-Path $dataAnalysisDir "daily_summary_latest.json"
        $dailySummaryDated  = Join-Path $dataAnalysisDir ("daily_summary_{0}.json" -f $Date)

        if (-not (Copy-IfExists -SourcePath $latestJson -DestinationPath $dailyNewsLatest)) {
            Write-Warning "latest.json not found; daily_news alias was not created."
        }
        Copy-IfExists -SourcePath $dailyNewsLatest -DestinationPath $dailyNewsDated | Out-Null

        if (-not (Copy-IfExists -SourcePath $summaryJson -DestinationPath $dailySummaryLatest)) {
            Write-Warning "summary.json not found; daily_summary alias was not created."
        }
        Copy-IfExists -SourcePath $dailySummaryLatest -DestinationPath $dailySummaryDated | Out-Null

        Copy-IfExists -SourcePath $dailyNewsLatest -DestinationPath (Join-Path $analysisDir "daily_news_latest.json") | Out-Null
        Copy-IfExists -SourcePath $dailySummaryLatest -DestinationPath (Join-Path $analysisDir "daily_summary_latest.json") | Out-Null

        if (Test-Path -LiteralPath $summaryJson) {
            $summaryMaterializer = @'
import json
from pathlib import Path

summary_path = Path(r"data\world_politics\analysis\summary.json")
if not summary_path.exists():
    raise SystemExit(0)

data = json.loads(summary_path.read_text(encoding="utf-8"))

def pick_text(obj):
    if not isinstance(obj, dict):
        return ""
    for key in ("summary", "text", "daily_summary", "body", "overview"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

summary_text = pick_text(data)

if not summary_text:
    anchors = [str(x).strip() for x in data.get("anchors", []) if str(x).strip()]
    urls = data.get("new_urls", []) if isinstance(data.get("new_urls"), list) else []
    n_events = data.get("n_events", 0)
    top_titles = []
    ys = data.get("yesterday_summary", {})
    if isinstance(ys, dict):
        titles = ys.get("titles", [])
        if isinstance(titles, list):
            top_titles = [str(x).strip() for x in titles[:3] if str(x).strip()]

    anchor_part = ", ".join(anchors[:5]) if anchors else "global developments"
    title_part = "; ".join(top_titles) if top_titles else ""
    pieces = [
        f"Observed {n_events} events.",
        f"Dominant anchors: {anchor_part}.",
    ]
    if title_part:
        pieces.append(f"Representative headlines: {title_part}.")
    if urls:
        pieces.append(f"New URLs detected: {len(urls)}.")
    summary_text = " ".join(pieces).strip()

data["summary"] = summary_text
data["text"] = summary_text
summary_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

daily_summary_path = Path(r"data\world_politics\analysis\daily_summary_latest.json")
if daily_summary_path.exists():
    ds = json.loads(daily_summary_path.read_text(encoding="utf-8"))
    if isinstance(ds, dict):
        ds["summary"] = summary_text
        ds["text"] = summary_text
        daily_summary_path.write_text(json.dumps(ds, ensure_ascii=False, indent=2), encoding="utf-8")
'@
            $tempPy = Join-Path $env:TEMP "genesis_summary_materializer.py"
            Set-Content -LiteralPath $tempPy -Value $summaryMaterializer -Encoding UTF8
            Write-Host "CMD: $python $tempPy"
            & $python $tempPy
            $exitCode = $LASTEXITCODE
            Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
            if ($exitCode -ne 0) {
                throw "summary materialization failed with exit code $exitCode."
            }
            Write-Log "[OK] summary text materialized into summary.json / daily_summary_latest.json"
            Copy-IfExists -SourcePath $dailySummaryLatest -DestinationPath $dailySummaryDated | Out-Null
            Copy-IfExists -SourcePath $dailySummaryLatest -DestinationPath (Join-Path $analysisDir "daily_summary_latest.json") | Out-Null
        }
    }

    Invoke-Step -Name "2) Build daily sentiment" -Action {
        if ($SkipSentiment) {
            Write-Log "[SKIP] sentiment skipped by flag."
            return
        }

        Invoke-PythonScript -PythonExe $python `
            -ScriptPath (Join-Path $scriptsDir "build_daily_sentiment.py") `
            -Arguments @("--date", $Date)
    }

    Invoke-Step -Name "3) Build digest view model" -Action {
        if ($SkipDigest) {
            Write-Log "[SKIP] digest skipped by flag."
            return
        }

        $digestCandidates = @(
            (Join-Path $scriptsDir "build_digest_view_model.py"),
            (Join-Path $scriptsDir "build_digest.py")
        )

        $digestScript = $digestCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if ($null -eq $digestScript -or [string]::IsNullOrWhiteSpace($digestScript)) {
            Write-Log "[SKIP] digest builder not found."
            return
        }

        Invoke-PythonScript -PythonExe $python -ScriptPath $digestScript -Arguments @("--date", $Date)
    }

    Invoke-Step -Name "4) Prediction pipeline" -Action {
        if ($SkipPrediction) {
            Write-Log "[SKIP] prediction skipped by flag."
            return
        }

        Invoke-PythonScript -PythonExe $python `
            -ScriptPath (Join-Path $scriptsDir "trend_engine.py")

        Invoke-PythonScript -PythonExe $python `
            -ScriptPath (Join-Path $scriptsDir "signal_engine.py")

        Invoke-PythonScript -PythonExe $python `
            -ScriptPath (Join-Path $scriptsDir "scenario_engine.py")

        Invoke-PythonScript -PythonExe $python `
            -ScriptPath (Join-Path $scriptsDir "prediction_engine.py")
    }

    Invoke-Step -Name "5) Publish prediction snapshot" -Action {
        $datedDir = Join-Path $predictionHistoryDir $Date
        Ensure-Dir -PathToEnsure $datedDir

        $predictionFiles = @(
            "trend_latest.json",
            "signal_latest.json",
            "early_warning_latest.json",
            "scenario_latest.json",
            "prediction_latest.json"
        )

        foreach ($name in $predictionFiles) {
            $src = Join-Path $predictionDir $name
            if (Test-Path -LiteralPath $src) {
                Copy-Item -LiteralPath $src -Destination (Join-Path $datedDir $name) -Force
                Write-Log "[OK] snapshot: $name"
            }
        }
    }

    Write-Log "run_daily_with_publish completed successfully."
    exit 0
}
catch {
    Write-Host "run_daily_with_publish finished with warnings/errors."
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
