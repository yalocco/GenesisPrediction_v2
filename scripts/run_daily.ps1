# scripts/run_daily.ps1
# GenesisPrediction v2 - Daily Runner (safe / "don't crash" edition)
#
# Recommended run:
#   powershell -ExecutionPolicy Bypass -File scripts\run_daily.ps1
# or:
#   .\scripts\run_daily.ps1

param(
  [string]$Date = "",
  [switch]$SkipOpenGui
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ----------------------------
# Helpers
# ----------------------------
function Write-Section([string]$title) {
  Write-Host ""
  Write-Host ("=" * 60)
  Write-Host $title
  Write-Host ("=" * 60)
}

function Write-Step([string]$title) {
  Write-Host ""
  Write-Host ("=== $title ===")
}

function Ensure-Dir([string]$path) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function Has-Prop($obj, [string]$name) {
  if ($null -eq $obj) { return $false }
  return $null -ne ($obj.PSObject.Properties.Match($name) | Select-Object -First 1)
}

function Read-JsonSafe([string]$path) {
  if (-not (Test-Path $path)) { return $null }

  $raw = Get-Content -Raw -LiteralPath $path -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }

  try {
    return ($raw | ConvertFrom-Json -Depth 64)
  } catch {
    $raw2 = $raw -replace "`r`n", "`n"
    try {
      return ($raw2 | ConvertFrom-Json -Depth 64)
    } catch {
      return $null
    }
  }
}

function Run-Py([string]$label, [string]$logPath, [string]$pyExe, [string[]]$pyArgs) {
  Write-Host "[INFO] $label"
  Ensure-Dir (Split-Path $logPath)

  # NOTE: must NOT use parameter name "$args" (conflicts with PowerShell automatic variable)
  & $pyExe @pyArgs 2>&1 | Tee-Object -FilePath $logPath -Append | Out-Host
  if ($LASTEXITCODE -ne 0) {
    throw "[ERR] $label failed (exit=$LASTEXITCODE). See log: $logPath"
  }
  Write-Host "[OK]  $label completed"
}

function Run-Cmd([string]$label, [string]$logPath, [string]$cmdLine) {
  Write-Host "[INFO] $label"
  Ensure-Dir (Split-Path $logPath)

  $full = "cmd.exe /V:ON /C `"$cmdLine 1>> `"$logPath`" 2>>&1 & exit /b !ERRORLEVEL!`""
  Invoke-Expression $full | Out-Null

  if ($LASTEXITCODE -ne 0) {
    throw "[ERR] $label failed (exit=$LASTEXITCODE). See log: $logPath"
  }
  Write-Host "[OK]  $label completed"
}

# ----------------------------
# Context
# ----------------------------
Write-Section "0) Context"

$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ROOT

$TZ = "Asia/Tokyo"

if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = (Get-Date).ToString("yyyy-MM-dd")
}

$PY = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$LOGDIR = Join-Path $ROOT "logs"
Ensure-Dir $LOGDIR

Write-Host ("[OK]  ROOT: {0}" -f $ROOT)
Write-Host ("[OK]  DATE: {0}" -f $Date)
Write-Host ("[OK]  TZ  : {0}" -f $TZ)
Write-Host ("[OK]  PY  : {0}" -f $PY)
Write-Host ("[OK]  LOG : {0}" -f $LOGDIR)

$SENT_LATEST = Join-Path $ROOT "data\world_politics\analysis\sentiment_latest.json"
$VM_DATED    = Join-Path $ROOT ("data\digest\view\{0}.json" -f $Date)
$VM_LATEST   = Join-Path $ROOT "data\digest\view\view_model_latest.json"

$log_fetcher  = Join-Path $LOGDIR ("fetcher_{0}.log" -f $Date)
$log_analyzer = Join-Path $LOGDIR ("analyzer_{0}.log" -f $Date)
$log_py       = Join-Path $LOGDIR ("daily_py_{0}.log" -f $Date)

# ----------------------------
# 1) Fetcher (docker)
# ----------------------------
Write-Step "1) Fetcher"
Run-Cmd "1) Fetcher" $log_fetcher "docker compose run --rm fetcher"

Write-Host ""
Write-Host ("---- tail 60 : {0} ----" -f $log_fetcher)
Get-Content -LiteralPath $log_fetcher -Tail 60 | Out-Host
Write-Host "---- end ----"

# ----------------------------
# 2) Analyzer (docker)
# ----------------------------
Write-Step "2) Analyzer"
Run-Cmd "2) Analyzer" $log_analyzer "docker compose run --rm analyzer"

Write-Host ""
Write-Host ("---- tail 120 : {0} ----" -f $log_analyzer)
Get-Content -LiteralPath $log_analyzer -Tail 120 | Out-Host
Write-Host "---- end ----"

# ----------------------------
# 3) Build Digest ViewModel (python)
# ----------------------------
Write-Step "3) Build Digest ViewModel"

$buildVM = "scripts\build_digest_view_model.py"
if (Test-Path $buildVM) {
  Run-Py "3) Build Digest ViewModel" $log_py $PY @($buildVM, "--date", $Date)
} else {
  Write-Host "[WARN] missing: $buildVM (skip)"
}

# ----------------------------
# 4) Normalize sentiment latest (python)
# ----------------------------
Write-Step "4) Normalize sentiment"

$normSent = "scripts\normalize_sentiment_latest.py"
if (Test-Path $normSent) {
  Run-Py "4) Normalize sentiment" $log_py $PY @($normSent)
} else {
  Write-Host "[WARN] missing: $normSent (skip)"
}

# ----------------------------
# 5) Patch sentiment summary into view model (python)
# ----------------------------
Write-Step "5) Patch sentiment summary (A spec)"

$patchVM = "scripts\ensure_view_model_sentiment_summary.py"
if (Test-Path $patchVM) {
  Run-Py "5) Patch sentiment summary" $log_py $PY @($patchVM, "--date", $Date)
} else {
  Write-Host "[WARN] missing: $patchVM (skip)"
}

# ----------------------------
# 6) Build sentiment timeseries (python)
# ----------------------------
Write-Step "6) Build sentiment timeseries"

$ts = "scripts\build_sentiment_timeseries_csv.py"
if (Test-Path $ts) {
  Run-Py "6) Build sentiment timeseries" $log_py $PY @($ts)
} else {
  Write-Host "[WARN] missing: $ts (skip)"
}

# ----------------------------
# 7) Sanity check (don't crash)
# ----------------------------
Write-Step "7) Sanity check"

$sentObj = Read-JsonSafe $SENT_LATEST
if ($null -ne $sentObj -and (Has-Prop $sentObj "today")) {
  $t = $sentObj.today
  Write-Host ""
  Write-Host "--- SENTIMENT (truth) ---"
  if (Has-Prop $t "articles")    { Write-Host ("articles    = {0}" -f $t.articles) }
  if (Has-Prop $t "risk")        { Write-Host ("risk        = {0}" -f $t.risk) }
  if (Has-Prop $t "positive")    { Write-Host ("positive    = {0}" -f $t.positive) }
  if (Has-Prop $t "uncertainty") { Write-Host ("uncertainty = {0}" -f $t.uncertainty) }
} else {
  Write-Host "[WARN] sentiment_latest.json missing or unexpected shape: $SENT_LATEST"
}

$vmObj = $null
if (Test-Path $VM_DATED) {
  $vmObj = Read-JsonSafe $VM_DATED
} elseif (Test-Path $VM_LATEST) {
  $vmObj = Read-JsonSafe $VM_LATEST
}

Write-Host ""
Write-Host "--- VIEW MODEL ---"
if ($null -eq $vmObj) {
  Write-Host "[WARN] view model not present (OK)"
} else {
  if (Has-Prop $vmObj "summary") {
    Write-Host "[OK]  view_model.summary present"
  } else {
    Write-Host "[WARN] view_model.summary not present (OK by design)"
  }
}

Write-Host "[OK]  Sanity check completed"

# ----------------------------
# 8) Open GUI
# ----------------------------
Write-Step "8) Open GUI"

$guiUrl = "http://127.0.0.1:8000/static/index.html?date=$Date"
Write-Host "[OK]  Open GUI: $guiUrl"

if (-not $SkipOpenGui) {
  try { Start-Process $guiUrl | Out-Null } catch { Write-Host "[WARN] could not open browser" }
}

Write-Host ""
Write-Host "DONE"
