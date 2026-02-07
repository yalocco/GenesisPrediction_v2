# scripts/report_sentiment_gaps.ps1
# Report which dates have:
# - raw daily news (data/world_politics/YYYY-MM-DD.json)
# - analysis daily_news (analysis/daily_news_YYYY-MM-DD.json)
# - analysis sentiment (analysis/sentiment_YYYY-MM-DD.json)
#
# Run:
#   powershell -ExecutionPolicy Bypass -File scripts/report_sentiment_gaps.ps1 -Days 30
#   powershell -ExecutionPolicy Bypass -File scripts/report_sentiment_gaps.ps1 -StartDate 2026-01-01 -EndDate 2026-02-07

param(
  [int]$Days = 30,
  [string]$StartDate = "",
  [string]$EndDate = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Parse-Date([string]$s) {
  $fmt = "yyyy-MM-dd"
  $provider = [System.Globalization.CultureInfo]::InvariantCulture
  $styles = [System.Globalization.DateTimeStyles]::None
  $tmp = New-Object DateTime
  if (-not [DateTime]::TryParseExact($s, $fmt, $provider, $styles, [ref]$tmp)) {
    throw "Invalid date '$s' (expected YYYY-MM-DD)"
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

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) { $scriptRoot = (Get-Location).Path }
$ROOT = (Resolve-Path (Join-Path $scriptRoot "..")).Path
Set-Location $ROOT

$end = if ([string]::IsNullOrWhiteSpace($EndDate)) { (Get-Date) } else { Parse-Date $EndDate }
$start =
  if (-not [string]::IsNullOrWhiteSpace($StartDate)) { Parse-Date $StartDate }
  else { $end.AddDays(-1 * [Math]::Max(0, $Days - 1)) }

$dates = Get-DateList $start $end

$rows = @()
foreach ($ds in $dates) {
  $raw = Join-Path $ROOT ("data\world_politics\{0}.json" -f $ds)
  $news = Join-Path $ROOT ("data\world_politics\analysis\daily_news_{0}.json" -f $ds)
  $sent = Join-Path $ROOT ("data\world_politics\analysis\sentiment_{0}.json" -f $ds)

  $rows += [pscustomobject]@{
    date = $ds
    raw_exists = (Test-Path $raw)
    daily_news_exists = (Test-Path $news)
    sentiment_exists = (Test-Path $sent)
  }
}

# Print gaps
Write-Host ""
Write-Host "=== GAPS (raw exists but sentiment missing) ==="
$g1 = $rows | Where-Object { $_.raw_exists -and (-not $_.sentiment_exists) }
$g1 | ForEach-Object { Write-Host ("- {0}" -f $_.date) }
Write-Host ("count: {0}" -f $g1.Count)

Write-Host ""
Write-Host "=== GAPS (raw missing) ==="
$g2 = $rows | Where-Object { -not $_.raw_exists }
$g2 | ForEach-Object { Write-Host ("- {0}" -f $_.date) }
Write-Host ("count: {0}" -f $g2.Count)

Write-Host ""
Write-Host "DONE"
