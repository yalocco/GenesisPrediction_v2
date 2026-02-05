# scripts/inspect_gui_inputs.ps1
# Verify what GUI is actually reading (files + HTTP responses)

[CmdletBinding()]
param(
  [string]$Date = "",
  [string]$BaseUrl = "http://127.0.0.1:8000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "[OK]  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "[ERR] $msg" -ForegroundColor Red; throw $msg }

function Resolve-Root {
  $root = Resolve-Path (Join-Path $PSScriptRoot "..")
  return $root.Path
}

function Show-File([string]$label, [string]$path) {
  if (-not (Test-Path $path)) {
    Warn "missing FILE ${label}: ${path}"
    return $null
  }
  $it = Get-Item $path
  Info "${label}: $($it.FullName)"
  Write-Host "      size=$($it.Length)  mtime=$($it.LastWriteTime)"
  return $it.FullName
}

function Read-Json([string]$path) {
  if (-not (Test-Path $path)) { return $null }
  $raw = Get-Content $path -Raw -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
  return $raw | ConvertFrom-Json
}

function Print-TodaySummary([string]$label, $json) {
  if ($null -eq $json) {
    Warn "${label}: json=null"
    return
  }

  $today = $null
  if ($json.PSObject.Properties.Name -contains "today") {
    $today = $json.today
  } else {
    $today = $json
  }

  Write-Host ""
  Write-Host "---- ${label} summary ----" -ForegroundColor Cyan
  Write-Host ("keys: " + ($today.PSObject.Properties.Name -join ", "))

  foreach ($k in @("date","articles","risk","positive","uncertainty","riskScore","posScore","uncScore")) {
    if ($today.PSObject.Properties.Name -contains $k) {
      Write-Host ("{0} = {1}" -f $k, $today.$k)
    }
  }
}

function Fetch-Http([string]$label, [string]$url) {
  Write-Host ""
  Write-Host "---- HTTP ${label} ----" -ForegroundColor Cyan
  Write-Host $url
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
    Info "status=$($r.StatusCode) bytes=$($r.RawContentLength)"
    return $r.Content
  } catch {
    Warn "HTTP failed: $($_.Exception.Message)"
    return $null
  }
}

# -----------------------------
# main
# -----------------------------
$ROOT = Resolve-Root
Set-Location $ROOT

if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = (Get-Date).ToString("yyyy-MM-dd")
}

Write-Host "============================================================"
Write-Host "inspect_gui_inputs.ps1  (date=$Date)"
Write-Host "ROOT=$ROOT"
Write-Host "BASE=$BaseUrl"
Write-Host "============================================================"

$path_analysis_vm_latest = Join-Path $ROOT "data\world_politics\analysis\view_model_latest.json"
$path_sent_latest       = Join-Path $ROOT "data\world_politics\analysis\sentiment_latest.json"

Show-File "analysis/view_model_latest.json" $path_analysis_vm_latest | Out-Null
Show-File "analysis/sentiment_latest.json"  $path_sent_latest       | Out-Null

$vm = Read-Json $path_analysis_vm_latest
$sent = Read-Json $path_sent_latest

Print-TodaySummary "FILE analysis/view_model_latest.json" $vm
Print-TodaySummary "FILE analysis/sentiment_latest.json"  $sent

Fetch-Http "analysis/view_model_latest.json" "$BaseUrl/analysis/view_model_latest.json" | Out-Null
Fetch-Http "analysis/sentiment_latest.json"  "$BaseUrl/analysis/sentiment_latest.json"  | Out-Null

Info "DONE"
