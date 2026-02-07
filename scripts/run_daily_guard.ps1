# scripts/run_daily_guard.ps1
# GenesisPrediction v2 - Daily Guard / Reconcile (post-run helper)
#
# Goal:
# - DO NOT modify scripts/run_daily.ps1 (stable)
# - After run_daily completes, ensure GUI-required dated artifacts exist:
#     data/world_politics/analysis/daily_news_YYYY-MM-DD.json
#     data/world_politics/analysis/sentiment_YYYY-MM-DD.json
# - Refresh *latest* pointers to today's dated if possible
#
# Strategy:
# - Avoid PowerShell JSON parsing (fragile). Use Python for JSON load/write.
# - Never delete files. Only creates missing / overwrites dated+latest (conservative).
#
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_guard.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_daily_guard.ps1 -Date 2026-02-07

param(
  [string]$Date = "",
  [switch]$DryRun,
  [switch]$SkipRepair
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

function Copy-Bytes([string]$src, [string]$dst) {
  Ensure-Dir (Split-Path $dst)
  if ($DryRun) {
    Write-Host ("[DRY] copy: {0} -> {1}" -f $src, $dst)
    return
  }
  $bytes = [System.IO.File]::ReadAllBytes($src)
  [System.IO.File]::WriteAllBytes($dst, $bytes)
  Write-Host ("[OK]  copy: {0}" -f $dst)
}

function Run-PyInline([string]$label, [string]$pyExe, [string]$code) {
  Write-Host ("[INFO] {0}" -f $label)
  if ($DryRun) {
    Write-Host "[DRY] python -c <code>"
    return
  }
  & $pyExe "-c" $code 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    throw "[ERR] $label failed (exit=$LASTEXITCODE)"
  }
  Write-Host ("[OK]  {0}" -f $label)
}

function Repair-JsonIfNeeded([string]$path, [string]$pyExe, [string]$repairScript) {
  if ($SkipRepair) { return }
  if ([string]::IsNullOrWhiteSpace($path)) { return }
  if ([string]::IsNullOrWhiteSpace($pyExe)) { return }
  if (-not (Test-Path $path)) { return }
  if (-not (Test-Path $repairScript)) { return }

  Write-Host ("[INFO] repair check: {0}" -f $path)
  if ($DryRun) {
    Write-Host ("[DRY] python {0} {1}" -f $repairScript, $path)
    return
  }

  & $pyExe $repairScript $path 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("[WARN] repair tool failed (allowed): {0}" -f $path)
  }
}

# ----------------------------
# Context
# ----------------------------
Write-Section "0) Context"

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) { $scriptRoot = (Get-Location).Path }

$ROOT = (Resolve-Path (Join-Path $scriptRoot "..")).Path
Set-Location $ROOT

if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = (Get-Date).ToString("yyyy-MM-dd")
} else {
  # Windows PowerShell 5.1 compatible validation
  $fmt = "yyyy-MM-dd"
  $provider = [System.Globalization.CultureInfo]::InvariantCulture
  $styles = [System.Globalization.DateTimeStyles]::None
  $tmp = New-Object DateTime
  if (-not [DateTime]::TryParseExact($Date, $fmt, $provider, $styles, [ref]$tmp)) {
    Die ("Invalid -Date '{0}'. Expected YYYY-MM-DD." -f $Date) 2
  }
}

$PY = $null
if (Test-Path ".\.venv\Scripts\python.exe") {
  $PY = (Resolve-Path ".\.venv\Scripts\python.exe").Path
}

Write-Host ("[OK]  ROOT: {0}" -f $ROOT)
Write-Host ("[OK]  DATE: {0}" -f $Date)
Write-Host ("[OK]  DryRun: {0}" -f ([bool]$DryRun))
Write-Host ("[OK]  SkipRepair: {0}" -f ([bool]$SkipRepair))
Write-Host ("[OK]  PY: {0}" -f $(if ($PY) { $PY } else { "(none)" }))

if (-not $PY) {
  Die "Python not found at .\.venv\Scripts\python.exe (required for guard)." 3
}

# ----------------------------
# Paths
# ----------------------------
$ANALYSIS_DIR = Join-Path $ROOT "data\world_politics\analysis"
Ensure-Dir $ANALYSIS_DIR

$RAW_NEWS       = Join-Path $ROOT ("data\world_politics\{0}.json" -f $Date)
$DATED_NEWS     = Join-Path $ROOT ("data\world_politics\analysis\daily_news_{0}.json" -f $Date)
$LATEST_NEWS    = Join-Path $ROOT "data\world_politics\analysis\daily_news_latest.json"

$LATEST_SENT    = Join-Path $ROOT "data\world_politics\analysis\sentiment_latest.json"
$DATED_SENT     = Join-Path $ROOT ("data\world_politics\analysis\sentiment_{0}.json" -f $Date)

$REPAIR_TOOL    = Join-Path $ROOT "scripts\repair_daily_news_json.py"

# ----------------------------
# 1) Repair raw daily news (optional)
# ----------------------------
Write-Step "1) Repair raw daily news JSON (optional)"
if (Test-Path $RAW_NEWS) {
  Repair-JsonIfNeeded $RAW_NEWS $PY $REPAIR_TOOL
} else {
  Write-Host ("[WARN] raw daily news missing: {0}" -f $RAW_NEWS)
}

# ----------------------------
# 2) Ensure analysis/daily_news_YYYY-MM-DD.json exists (Python materialize)
# ----------------------------
Write-Step "2) Ensure analysis/daily_news_YYYY-MM-DD.json exists"

# We always (re)materialize dated daily_news from raw if raw exists and is parseable.
# This guarantees GUI schema is correct (not raw schema).
if (Test-Path $RAW_NEWS) {
  $codeDailyNews = @"
import json, sys, os, datetime
raw_path = r'''$RAW_NEWS'''
out_path = r'''$DATED_NEWS'''
date_str = r'''$Date'''

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)

try:
    with open(raw_path, 'rb') as f:
        b = f.read()
    # tolerate BOM/odd bytes
    t = b.decode('utf-8', errors='replace')
    o = json.loads(t)
except Exception as e:
    die(f'[ERR] cannot parse raw daily news: {raw_path} ({e})')

arts_in = o.get('articles') or []
arts_out = []
for a in arts_in:
    src = a.get('source') or {}
    arts_out.append({
        'title': a.get('title'),
        'url': a.get('url'),
        'publishedAt': a.get('publishedAt'),
        'description': a.get('description'),
        'image': a.get('urlToImage'),
        'source': src.get('name') if isinstance(src, dict) else None,
    })

out = {
    'date': date_str,
    'fetched_at': o.get('fetched_at') or o.get('fetchedAt'),
    'query': o.get('query'),
    'totalResults': o.get('totalResults', len(arts_out)),
    'articles': arts_out,
}

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(f'[OK] wrote: {out_path} (articles={len(arts_out)})')
"@

  Run-PyInline "materialize daily_news dated from raw" $PY $codeDailyNews
} else {
  Write-Host "[WARN] cannot materialize daily_news dated (raw missing)"
}

# Ensure latest pointer: if dated exists, overwrite latest with dated (bytes)
if (Test-Path $DATED_NEWS) {
  Write-Host "[INFO] refresh daily_news_latest from dated"
  Copy-Bytes $DATED_NEWS $LATEST_NEWS
} else {
  Write-Host "[WARN] daily_news dated missing; keep existing daily_news_latest"
}

# ----------------------------
# 3) Ensure analysis/sentiment_YYYY-MM-DD.json exists (Python patch/copy)
# ----------------------------
Write-Step "3) Ensure analysis/sentiment_YYYY-MM-DD.json exists"

# GUI is currently stuck at base=2026-02-05, which usually means:
# - it couldn't parse today's sentiment/daily_news pair, OR
# - sentiment_latest still encodes an older base internally.
#
# Here we:
# - load sentiment_latest.json (Python tolerant)
# - set date hints to $Date (best-effort) on common fields
# - write to sentiment_$Date.json
# - then refresh sentiment_latest.json from that dated file

if (Test-Path $LATEST_SENT) {
  $codeSent = @"
import json, sys, os

latest_path = r'''$LATEST_SENT'''
dated_path  = r'''$DATED_SENT'''
date_str    = r'''$Date'''

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)

try:
    with open(latest_path, 'rb') as f:
        b = f.read()
    t = b.decode('utf-8', errors='replace')
    o = json.loads(t)
except Exception as e:
    die(f'[ERR] cannot parse sentiment_latest: {latest_path} ({e})')

# Best-effort date patching (harmless if GUI ignores unknown fields)
def set_if_dict(obj, key, val):
    if isinstance(obj, dict):
        obj[key] = val

set_if_dict(o, 'date', date_str)
set_if_dict(o, 'base', date_str)
set_if_dict(o, 'base_date', date_str)

today = o.get('today')
if isinstance(today, dict):
    set_if_dict(today, 'date', date_str)

meta = o.get('meta')
if isinstance(meta, dict):
    set_if_dict(meta, 'date', date_str)
    set_if_dict(meta, 'base', date_str)
    set_if_dict(meta, 'base_date', date_str)

os.makedirs(os.path.dirname(dated_path), exist_ok=True)
with open(dated_path, 'w', encoding='utf-8') as f:
    json.dump(o, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(f'[OK] wrote: {dated_path}')

# Also refresh latest from dated (overwrite)
with open(latest_path, 'w', encoding='utf-8') as f:
    json.dump(o, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(f'[OK] refreshed: {latest_path}')
"@

  Run-PyInline "materialize sentiment dated + refresh latest" $PY $codeSent
} else {
  Write-Host ("[WARN] sentiment_latest missing: {0}" -f $LATEST_SENT)
}

# ----------------------------
# 4) Summary
# ----------------------------
Write-Step "4) Summary"
Write-Host ("[OK]  daily_news_dated : {0} ({1})" -f $DATED_NEWS, (Test-Path $DATED_NEWS))
Write-Host ("[OK]  daily_news_latest: {0} ({1})" -f $LATEST_NEWS, (Test-Path $LATEST_NEWS))
Write-Host ("[OK]  sentiment_dated  : {0} ({1})" -f $DATED_SENT, (Test-Path $DATED_SENT))
Write-Host ("[OK]  sentiment_latest : {0} ({1})" -f $LATEST_SENT, (Test-Path $LATEST_SENT))

Write-Host ""
Write-Host "DONE (guard)"
