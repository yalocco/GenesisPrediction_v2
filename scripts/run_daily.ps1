# scripts/run_daily.ps1
# GenesisPrediction v2 - Daily Runner (commercial-grade / "don't crash" edition)
#
# Goals
# - Deterministic "today" date handling (single source)
# - Dependency checks (docker/compose/python/files)
# - Low-noise logs (stderr captured, tail shown)
# - ExitCode correctness (fail fast with one-line cause)
# - Re-run safe (idempotent-ish; skips missing optional steps)
# - JSON read defense (encoding/ANSI/garbage prefix/suffix/huge)
#
# Recommended run:
#   powershell -ExecutionPolicy Bypass -File scripts\run_daily.ps1
# or:
#   .\scripts\run_daily.ps1
#
# Options:
#   -Date "YYYY-MM-DD"   (default: today in local clock)
#   -SkipOpenGui         (do not open browser)
#   -VerboseLogs         (show more lines of tail for each step)

param(
  [string]$Date = "",
  [switch]$SkipOpenGui,
  [switch]$VerboseLogs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ----------------------------
# Helpers (logging / checks)
# ----------------------------
function Write-Section([string]$title) {
  Write-Host ""
  Write-Host ("=" * 72)
  Write-Host $title
  Write-Host ("=" * 72)
}

function Write-Step([string]$title) {
  Write-Host ""
  Write-Host ("--- {0} ---" -f $title)
}

function Ensure-Dir([string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return }
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function Die([string]$msg, [int]$code = 1) {
  Write-Host ""
  Write-Host ("[FATAL] {0}" -f $msg)
  exit $code
}

function Has-Prop($obj, [string]$name) {
  if ($null -eq $obj) { return $false }
  return $null -ne ($obj.PSObject.Properties.Match($name) | Select-Object -First 1)
}

function Trim-Ansi([string]$s) {
  if ($null -eq $s) { return "" }
  # Remove ANSI escape sequences
  return ([regex]::Replace($s, "`e\[[0-9;]*[A-Za-z]", ""))
}

function Extract-JsonPayload([string]$raw) {
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }

  $s = Trim-Ansi $raw
  $s = $s.Replace("`r`n", "`n")

  $iObj = $s.IndexOf("{")
  $iArr = $s.IndexOf("[")

  if ($iObj -lt 0 -and $iArr -lt 0) { return $null }

  $start = 0
  if ($iObj -ge 0 -and $iArr -ge 0) { $start = [Math]::Min($iObj, $iArr) }
  elseif ($iObj -ge 0) { $start = $iObj }
  else { $start = $iArr }

  $endObj = $s.LastIndexOf("}")
  $endArr = $s.LastIndexOf("]")

  $end = -1
  if ($endObj -ge 0 -and $endArr -ge 0) { $end = [Math]::Max($endObj, $endArr) }
  elseif ($endObj -ge 0) { $end = $endObj }
  else { $end = $endArr }

  if ($end -le $start) { return $null }

  return $s.Substring($start, $end - $start + 1)
}

function Read-JsonSafe([string]$path, [int]$maxBytes = 15MB) {
  if (-not (Test-Path $path)) { return $null }

  try {
    $fi = Get-Item -LiteralPath $path
    if ($fi.Length -gt $maxBytes) {
      Write-Host ("[WARN] JSON too large, skip parse: {0} ({1} bytes)" -f $path, $fi.Length)
      return $null
    }
  } catch {
    # ignore size check errors
  }

  $raw = ""
  try {
    $raw = Get-Content -Raw -LiteralPath $path -Encoding UTF8
  } catch {
    try {
      $raw = Get-Content -Raw -LiteralPath $path
    } catch {
      return $null
    }
  }

  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }

  $payload = Extract-JsonPayload $raw
  if ($null -eq $payload) { return $null }

  try {
    return ($payload | ConvertFrom-Json -Depth 64)
  } catch {
    return $null
  }
}

function Require-Command([string]$cmd, [string]$hint) {
  $c = Get-Command $cmd -ErrorAction SilentlyContinue
  if ($null -eq $c) {
    Die ("Missing command: {0}. {1}" -f $cmd, $hint) 2
  }
}

function Require-File([string]$path, [string]$hint) {
  if (-not (Test-Path $path)) {
    Die ("Missing file: {0}. {1}" -f $path, $hint) 3
  }
}

function Tail-File([string]$path, [int]$lines) {
  if (-not (Test-Path $path)) { return }
  Write-Host ""
  Write-Host ("---- tail {0}: {1} ----" -f $lines, $path)
  try { Get-Content -LiteralPath $path -Tail $lines | Out-Host } catch { }
  Write-Host "---- end ----"
}

# Use Start-Process to avoid NativeCommandError noise when tools write to stderr (e.g., docker compose "Creating/Starting").
function Run-ProcessToLog(
  [string]$label,
  [string]$logPath,
  [string]$filePath,
  [string[]]$arguments,
  [string]$workingDir
) {
  Write-Host ("[INFO] {0}" -f $label)
  Ensure-Dir (Split-Path $logPath)

  $tmpOut = $logPath + ".out.tmp"
  $tmpErr = $logPath + ".err.tmp"

  if (Test-Path $tmpOut) { Remove-Item -Force -LiteralPath $tmpOut -ErrorAction SilentlyContinue }
  if (Test-Path $tmpErr) { Remove-Item -Force -LiteralPath $tmpErr -ErrorAction SilentlyContinue }

  $argLine = ($arguments | ForEach-Object {
    if ($_ -match '\s') { '"' + ($_ -replace '"','\"') + '"' } else { $_ }
  }) -join " "

  # Header
  Add-Content -LiteralPath $logPath -Encoding UTF8 -Value ("`n[{0}] {1}`nCMD: {2} {3}`n" -f (Get-Date).ToString("s"), $label, $filePath, $argLine)

  $p = Start-Process -FilePath $filePath `
                     -ArgumentList $arguments `
                     -WorkingDirectory $workingDir `
                     -NoNewWindow `
                     -PassThru `
                     -Wait `
                     -RedirectStandardOutput $tmpOut `
                     -RedirectStandardError  $tmpErr

  # Append captured output to main log, then cleanup tmp
  if (Test-Path $tmpOut) {
    Get-Content -LiteralPath $tmpOut -Raw | Add-Content -LiteralPath $logPath -Encoding UTF8
    Remove-Item -Force -LiteralPath $tmpOut -ErrorAction SilentlyContinue
  }
  if (Test-Path $tmpErr) {
    Get-Content -LiteralPath $tmpErr -Raw | Add-Content -LiteralPath $logPath -Encoding UTF8
    Remove-Item -Force -LiteralPath $tmpErr -ErrorAction SilentlyContinue
  }

  Add-Content -LiteralPath $logPath -Encoding UTF8 -Value ("`nEXIT: {0}`n" -f $p.ExitCode)

  if ($p.ExitCode -ne 0) {
    throw ("[ERR] {0} failed (exit={1}). See log: {2}" -f $label, $p.ExitCode, $logPath)
  }
  Write-Host ("[OK]  {0} completed" -f $label)
}

function Run-DockerCompose([string]$label, [string]$logPath, [string]$service, [string]$workingDir) {
  # Prefer "docker compose" (plugin) if available; otherwise fall back to "docker-compose".
  $docker = (Get-Command docker -ErrorAction SilentlyContinue)
  if ($null -ne $docker) {
    Run-ProcessToLog $label $logPath "docker" @("compose","run","--rm",$service) $workingDir
    return
  }
  $dc = (Get-Command docker-compose -ErrorAction SilentlyContinue)
  if ($null -ne $dc) {
    Run-ProcessToLog $label $logPath "docker-compose" @("run","--rm",$service) $workingDir
    return
  }
  Die "Docker not found. Install Docker Desktop and ensure docker is on PATH." 2
}

function Guess-PyArgsForScript([string]$scriptPath, [string]$dateStr) {
  # Return best-effort args for scripts whose CLI differs.
  # Strategy: read file text and detect known options.
  try {
    $txt = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8
  } catch {
    try { $txt = Get-Content -LiteralPath $scriptPath -Raw } catch { return @() }
  }

  if ($txt -match '["'']--date["'']' -or $txt -match 'add_argument\(\s*["'']--date["'']') {
    return @("--date", $dateStr)
  }

  if ($txt -match '["'']--day["'']' -or $txt -match 'add_argument\(\s*["'']--day["'']') {
    return @("--day", $dateStr)
  }

  # If it looks like it expects input/output paths, don't guess (avoid writing wrong files).
  # Run with no args and let it decide defaults; if it fails, the log will show the required usage.
  return @()
}

function Run-PythonScript([string]$label, [string]$logPath, [string]$pyExe, [string]$scriptRel, [string]$rootDir, [string]$dateStr) {
  if (-not (Test-Path $scriptRel)) {
    Write-Host ("[WARN] missing: {0} (skip)" -f $scriptRel)
    return
  }

  $args = @($scriptRel) + (Guess-PyArgsForScript $scriptRel $dateStr)
  Run-ProcessToLog $label $logPath $pyExe $args $rootDir
}

# ----------------------------
# Context (root, date, venv)
# ----------------------------
Write-Section "0) Context"

$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ROOT

# Date: single source of truth
if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = (Get-Date).ToString("yyyy-MM-dd")
} else {
  # Validate date format
  $parsed = $null
  if (-not [DateTime]::TryParseExact($Date, "yyyy-MM-dd", $null, [Globalization.DateTimeStyles]::None, [ref]$parsed)) {
    Die ("Invalid -Date '{0}'. Expected YYYY-MM-DD." -f $Date) 4
  }
}

$LOGDIR = Join-Path $ROOT "logs"
Ensure-Dir $LOGDIR

$log_fetcher  = Join-Path $LOGDIR ("fetcher_{0}.log" -f $Date)
$log_analyzer = Join-Path $LOGDIR ("analyzer_{0}.log" -f $Date)
$log_py       = Join-Path $LOGDIR ("daily_py_{0}.log" -f $Date)

# Dependencies
Require-File ".\.venv\Scripts\python.exe" "Create venv and install requirements (python.txt / requirements.txt) in repo root."
$PY = (Resolve-Path ".\.venv\Scripts\python.exe").Path

# docker is required for fetcher/analyzer
Require-Command "docker" "Install Docker Desktop and restart shell so PATH is updated."

Write-Host ("[OK]  ROOT: {0}" -f $ROOT)
Write-Host ("[OK]  DATE: {0}" -f $Date)
Write-Host ("[OK]  PY  : {0}" -f $PY)
Write-Host ("[OK]  LOG : {0}" -f $LOGDIR)
Write-Host ("[OK]  SkipOpenGui: {0}" -f ([bool]$SkipOpenGui))
Write-Host ("[OK]  VerboseLogs: {0}" -f ([bool]$VerboseLogs))

# Important paths
$SENT_LATEST = Join-Path $ROOT "data\world_politics\analysis\sentiment_latest.json"
$VM_DATED    = Join-Path $ROOT ("data\digest\view\{0}.json" -f $Date)
$VM_LATEST   = Join-Path $ROOT "data\digest\view\view_model_latest.json"

# Tail length
$tailFetch = $(if ($VerboseLogs) { 160 } else { 60 })
$tailAna   = $(if ($VerboseLogs) { 240 } else { 120 })
$tailPy    = $(if ($VerboseLogs) { 200 } else { 80 })

# ----------------------------
# 1) Fetcher (docker)
# ----------------------------
Write-Step "1) Fetcher (docker compose run --rm fetcher)"
Run-DockerCompose "1) Fetcher" $log_fetcher "fetcher" $ROOT
Tail-File $log_fetcher $tailFetch

# ----------------------------
# 2) Analyzer (docker)
# ----------------------------
Write-Step "2) Analyzer (docker compose run --rm analyzer)"
Run-DockerCompose "2) Analyzer" $log_analyzer "analyzer" $ROOT
Tail-File $log_analyzer $tailAna

# ----------------------------
# 3) Build Digest ViewModel (python)
# ----------------------------
Write-Step "3) Build Digest ViewModel (python)"
Run-PythonScript "3) Build Digest ViewModel" $log_py $PY "scripts\build_digest_view_model.py" $ROOT $Date

# ----------------------------
# 4) Normalize sentiment latest (python)
# ----------------------------
Write-Step "4) Normalize sentiment latest (python)"
Run-PythonScript "4) Normalize sentiment latest" $log_py $PY "scripts\normalize_sentiment_latest.py" $ROOT $Date

# ----------------------------
# 5) Patch sentiment summary into view model (python)
# ----------------------------
Write-Step "5) Patch sentiment summary (A spec) (python)"
Run-PythonScript "5) Patch sentiment summary" $log_py $PY "scripts\ensure_view_model_sentiment_summary.py" $ROOT $Date

# ----------------------------
# 6) Build sentiment timeseries (python)
# ----------------------------
Write-Step "6) Build sentiment timeseries (python)"
# NOTE:
# - This step is often where "Usage:" appears if args mismatch.
# - We do best-effort arg guessing by reading the script.
# - If it still fails, the log will show required usage in one place.
Run-PythonScript "6) Build sentiment timeseries" $log_py $PY "scripts\build_sentiment_timeseries_csv.py" $ROOT $Date

Tail-File $log_py $tailPy

# ----------------------------
# 7) Sanity check (non-fatal by design)
# ----------------------------
Write-Step "7) Sanity check (non-fatal)"

# Sentiment shape (allow minor evolution; only require 'today' object if present)
$sentObj = Read-JsonSafe $SENT_LATEST
if ($null -ne $sentObj -and (Has-Prop $sentObj "today")) {
  $t = $sentObj.today
  Write-Host ""
  Write-Host "--- SENTIMENT (today) ---"
  if (Has-Prop $t "articles")    { Write-Host ("articles    = {0}" -f $t.articles) }
  if (Has-Prop $t "risk")        { Write-Host ("risk        = {0}" -f $t.risk) }
  if (Has-Prop $t "positive")    { Write-Host ("positive    = {0}" -f $t.positive) }
  if (Has-Prop $t "uncertainty") { Write-Host ("uncertainty = {0}" -f $t.uncertainty) }
} else {
  Write-Host ("[WARN] sentiment_latest.json missing/unparseable/or unexpected shape (allowed): {0}" -f $SENT_LATEST)
}

# View model shape (explicitly tolerant)
$vmObj = $null
$vmSource = ""
if (Test-Path $VM_DATED) {
  $vmObj = Read-JsonSafe $VM_DATED
  $vmSource = $VM_DATED
} elseif (Test-Path $VM_LATEST) {
  $vmObj = Read-JsonSafe $VM_LATEST
  $vmSource = $VM_LATEST
}

Write-Host ""
Write-Host "--- VIEW MODEL ---"
if ($null -eq $vmObj) {
  Write-Host "[WARN] view model not present/unparseable (allowed)"
} else {
  Write-Host ("[OK]  view model loaded: {0}" -f $vmSource)

  # "summary" may or may not exist depending on schema evolution — tolerate.
  if (Has-Prop $vmObj "summary") {
    Write-Host "[OK]  view_model.summary present"
  } else {
    Write-Host "[OK]  view_model.summary absent (allowed by design)"
  }

  # Optional: quick presence checks that should remain stable
  if (Has-Prop $vmObj "date") {
    Write-Host ("[OK]  view_model.date = {0}" -f $vmObj.date)
  } else {
    Write-Host "[OK]  view_model.date missing (allowed)"
  }
}

Write-Host "[OK]  Sanity check completed (non-fatal warnings only)"

# ----------------------------
# 8) Open GUI
# ----------------------------
Write-Step "8) Open GUI"

$guiUrl = "http://127.0.0.1:8000/static/index.html?date=$Date"
Write-Host ("[OK]  Open GUI: {0}" -f $guiUrl)

if (-not $SkipOpenGui) {
  try { Start-Process $guiUrl | Out-Null }
  catch { Write-Host "[WARN] could not open browser (ignored)" }
}

Write-Host ""
Write-Host "DONE"
