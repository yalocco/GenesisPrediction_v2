# scripts/backfill_gui_artifacts.ps1
# Backfill GUI artifacts safely:
# - materialize analysis/daily_news_YYYY-MM-DD.json from raw data/world_politics/YYYY-MM-DD.json
# - rebuild analysis/sentiment_timeseries.csv from existing analysis/sentiment_YYYY-MM-DD.json
# - NEVER deletes anything
#
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts/backfill_gui_artifacts.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/backfill_gui_artifacts.ps1 -Days 30
#   powershell -ExecutionPolicy Bypass -File scripts/backfill_gui_artifacts.ps1 -StartDate 2026-01-01 -EndDate 2026-02-07

param(
  [int]$Days = 21,
  [string]$StartDate = "",
  [string]$EndDate = "",
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section([string]$title) {
  Write-Host ""
  Write-Host ("=" * 72)
  Write-Host $title
  Write-Host ("=" * 72)
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

function Parse-Date([string]$s) {
  $fmt = "yyyy-MM-dd"
  $provider = [System.Globalization.CultureInfo]::InvariantCulture
  $styles = [System.Globalization.DateTimeStyles]::None
  $tmp = New-Object DateTime
  if (-not [DateTime]::TryParseExact($s, $fmt, $provider, $styles, [ref]$tmp)) {
    Die ("Invalid date '{0}' (expected YYYY-MM-DD)" -f $s) 2
  }
  return $tmp
}

function Get-DateList([DateTime]$start, [DateTime]$end) {
  $dates = @()
  $d = $start.Date
  $e = $end.Date
  while ($d -le $e) {
    $dates += $d.ToString("yyyy-MM-dd")
    $d = $d.AddDays(1)
  }
  return $dates
}

# ----------------------------
# Context
# ----------------------------
Write-Section "0) Context"

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) { $scriptRoot = (Get-Location).Path }

$ROOT = (Resolve-Path (Join-Path $scriptRoot "..")).Path
Set-Location $ROOT

$PY = $null
if (Test-Path ".\.venv\Scripts\python.exe") {
  $PY = (Resolve-Path ".\.venv\Scripts\python.exe").Path
} else {
  Die "Python not found at .\.venv\Scripts\python.exe" 3
}

$analysisDir = Join-Path $ROOT "data\world_politics\analysis"
Ensure-Dir $analysisDir

Write-Host ("[OK]  ROOT: {0}" -f $ROOT)
Write-Host ("[OK]  PY  : {0}" -f $PY)
Write-Host ("[OK]  DryRun: {0}" -f ([bool]$DryRun))

# Determine date range
$end = if ([string]::IsNullOrWhiteSpace($EndDate)) { (Get-Date) } else { Parse-Date $EndDate }
$start =
  if (-not [string]::IsNullOrWhiteSpace($StartDate)) { Parse-Date $StartDate }
  else { $end.AddDays(-1 * [Math]::Max(0, $Days - 1)) }

$dates = Get-DateList $start $end
Write-Host ("[OK]  Range: {0} .. {1} ({2} days)" -f $dates[0], $dates[-1], $dates.Count)

# ----------------------------
# 1) Materialize daily_news_YYYY-MM-DD.json from raw
# ----------------------------
Write-Section "1) Backfill daily_news_YYYY-MM-DD.json (from raw)"

$missingRaw = @()
$madeNews = 0
$skippedNews = 0

foreach ($ds in $dates) {
  $raw = Join-Path $ROOT ("data\world_politics\{0}.json" -f $ds)
  $dst = Join-Path $ROOT ("data\world_politics\analysis\daily_news_{0}.json" -f $ds)

  if (Test-Path $dst) {
    $skippedNews++
    continue
  }
  if (-not (Test-Path $raw)) {
    $missingRaw += $ds
    continue
  }

  $code = @"
import json, sys, os
raw_path = r'''$raw'''
out_path = r'''$dst'''
date_str = r'''$ds'''

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)

try:
    with open(raw_path, 'rb') as f:
        b = f.read()
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

  if ($DryRun) {
    Write-Host ("[DRY] make daily_news: {0}" -f $dst)
  } else {
    & $PY "-c" $code 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "[ERR] daily_news materialize failed for $ds" }
  }
  $madeNews++
}

Write-Host ("[OK]  made daily_news: {0}" -f $madeNews)
Write-Host ("[OK]  skipped (already): {0}" -f $skippedNews)
Write-Host ("[WARN] missing raw days : {0}" -f $missingRaw.Count)
if ($missingRaw.Count -gt 0) {
  Write-Host ("       " + ($missingRaw -join ", "))
}

# ----------------------------
# 2) Rebuild sentiment_timeseries.csv from existing sentiment_YYYY-MM-DD.json
# ----------------------------
Write-Section "2) Rebuild sentiment_timeseries.csv (from existing sentiment_YYYY-MM-DD.json)"

$outCsv = Join-Path $ROOT "data\world_politics\analysis\sentiment_timeseries.csv"

$codeTs = @"
import os, re, json, csv, sys
root = r'''$analysisDir'''
out_csv = r'''$outCsv'''

rx = re.compile(r'^sentiment_(\d{4}-\d{2}-\d{2})\.json$')
rows = []

def pick(d, keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default

def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

files = []
for name in os.listdir(root):
    m = rx.match(name)
    if m:
        files.append((m.group(1), os.path.join(root, name)))
files.sort()

missing_fields = 0

for ds, path in files:
    try:
        with open(path, 'rb') as f:
            b = f.read()
        t = b.decode('utf-8', errors='replace')
        obj = json.loads(t)
    except Exception:
        continue

    # Common shapes:
    # - obj['today'] has {articles,risk,positive,uncertainty}
    # - or top-level has those
    today = obj.get('today') if isinstance(obj, dict) else None
    src = today if isinstance(today, dict) else (obj if isinstance(obj, dict) else {})

    articles = pick(src, ['articles', 'n_articles', 'count'])
    risk = pick(src, ['risk'])
    pos = pick(src, ['positive', 'pos'])
    unc = pick(src, ['uncertainty', 'unc'])

    # normalize
    a_i = None
    try:
        a_i = int(articles) if articles is not None else None
    except Exception:
        a_i = None

    r_f = to_float(risk)
    p_f = to_float(pos)
    u_f = to_float(unc)

    if a_i is None or r_f is None or p_f is None or u_f is None:
        missing_fields += 1
        # still write minimal row if possible
        # but if totally unusable, skip
        if a_i is None:
            continue
        if r_f is None: r_f = 0.0
        if p_f is None: p_f = 0.0
        if u_f is None: u_f = 0.0

    rows.append({
        'date': ds,
        'articles': a_i,
        'risk': f'{r_f:.6f}',
        'positive': f'{p_f:.6f}',
        'uncertainty': f'{u_f:.6f}',
    })

os.makedirs(os.path.dirname(out_csv), exist_ok=True)
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['date','articles','risk','positive','uncertainty'])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f'[OK] wrote: {out_csv} (rows={len(rows)})')
if missing_fields:
    print(f'[WARN] some sentiment files missing fields; filled defaults where possible: {missing_fields}')
"@

if ($DryRun) {
  Write-Host ("[DRY] rebuild timeseries: {0}" -f $outCsv)
} else {
  & $PY "-c" $codeTs 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) { throw "[ERR] timeseries rebuild failed" }
}

Write-Host ""
Write-Host "DONE (backfill)"
