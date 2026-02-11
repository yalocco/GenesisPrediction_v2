# scripts/deploy_labos.ps1
# ConoHa WING deploy - stable, re-runnable (argv-array safe)
#
# Key points:
# - Avoid $Host reserved variable collision (use $sshHost)
# - Force bash on remote (WING may default to csh/tcsh)
# - Upload tar to HOME first, then move into release dir
# - Publish into public_html/<subdomain>
# - Use argv arrays for ssh/scp to avoid quoting hell
# - FIX: ensure /analysis/digest_latest.json exists (alias from common filenames or fallback {})

[CmdletBinding()]
param(
  [ValidateSet("dev","prod")]
  [string]$Profile = "dev",
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }
function Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Ok([string]$msg)   { Write-Host "[OK] $msg" -ForegroundColor Green }

function Require-Command([string]$name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { Fail "command not found: $name" }
}

function Run([string]$label, [string[]]$argv) {
  $cmdline = ($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
  Info $label
  if ($DryRun) { Info ("DRYRUN: {0}" -f $cmdline); return }

  & $argv[0] @($argv[1..($argv.Length-1)])
  if ($LASTEXITCODE -ne 0) { Fail "$label failed (exit=$LASTEXITCODE)" }
}

Require-Command "ssh"
Require-Command "scp"
Require-Command "tar"

$cfgPath = Join-Path $PSScriptRoot "deploy_labos.config.ps1"
if (-not (Test-Path $cfgPath)) { Fail "missing config file: $cfgPath" }
. $cfgPath

if (-not $DEPLOY_PROFILES.ContainsKey($Profile)) {
  Fail "profile not found: $Profile. Available: $($DEPLOY_PROFILES.Keys -join ', ')"
}
$p = $DEPLOY_PROFILES[$Profile]

$required = @("Name","Host","User","Port","KeyPath","LocalDir","RemoteBaseDir","RemoteReleaseName","WebRootDirName")
foreach ($k in $required) {
  if (-not $p.ContainsKey($k) -or [string]::IsNullOrWhiteSpace([string]$p[$k])) {
    Fail "config error: missing '$k' in profile '$Profile'"
  }
}

$name        = [string]$p["Name"]
$sshHost     = [string]$p["Host"]   # do NOT use $Host/$host
$user        = [string]$p["User"]
$port        = [int]$p["Port"]
$keyPath     = [string]$p["KeyPath"]
$localDir    = (Resolve-Path ([string]$p["LocalDir"])).Path
$homeDir     = [string]$p["RemoteBaseDir"]
$releaseName = [string]$p["RemoteReleaseName"]
$webDirName  = [string]$p["WebRootDirName"]

$mirrorRootFiles = $true
if ($p.ContainsKey("MirrorRootFiles")) { $mirrorRootFiles = [bool]$p["MirrorRootFiles"] }

if (-not (Test-Path $keyPath)) { Fail "SSH key not found: $keyPath" }
if (-not (Test-Path $localDir)) { Fail "LocalDir not found: $localDir" }

$remoteReleaseDir = "$homeDir/releases/$releaseName"
$remoteWebRoot    = "$homeDir/public_html/$webDirName"
$remoteTarget     = ("{0}@{1}" -f $user, $sshHost)

Info ("Deploy: {0} ({1})" -f $name, $Profile)
Info ("Remote: {0}:{1}" -f $remoteTarget, $port)
Info ("ReleaseDir: {0}" -f $remoteReleaseDir)
Info ("WebRoot   : {0}" -f $remoteWebRoot)
Info ("MirrorRootFiles: {0}" -f $mirrorRootFiles)

$sshBase = @("ssh","-p","$port","-i",$keyPath,$remoteTarget)
$scpBase = @("scp","-P","$port","-i",$keyPath)

# Build tar
$tmpTar = Join-Path $env:TEMP "labos_release.tar.gz"
if (Test-Path $tmpTar) { Remove-Item $tmpTar -Force }

Run "tar create" @("tar","-czf",$tmpTar,"-C",$localDir,".")

# remote mkdir (bash -lc "<cmd>")
$mkdirCmd = 'set -e; mkdir -p "' + $homeDir + '/releases" "' + $remoteReleaseDir + '" "' + $remoteWebRoot + '/static" "' + $remoteWebRoot + '/analysis" "' + $remoteWebRoot + '/error"'
Run "remote mkdir" ($sshBase + @("bash","-lc",$mkdirCmd))

# scp upload to HOME
$remoteHomeTar = ("{0}:{1}/labos_release.tar.gz" -f $remoteTarget, $homeDir)
Run "scp upload (to HOME)" ($scpBase + @($tmpTar, $remoteHomeTar))

# move+extract
$extractCmd = 'set -e; mv "' + $homeDir + '/labos_release.tar.gz" "' + $remoteReleaseDir + '/release.tar.gz"; cd "' + $remoteReleaseDir + '"; tar -xzf release.tar.gz; rm -f release.tar.gz'
Run "remote move+extract" ($sshBase + @("bash","-lc",$extractCmd))

# publish
$mirrorFlag = if ($mirrorRootFiles) { "1" } else { "0" }

# --- IMPORTANT: ensure digest_latest.json exists in STAGE/analysis to avoid 404 on GUI
$publishCmd =
  'set -e;' +
  ' STAGE="' + $remoteReleaseDir + '";' +
  ' WEBROOT="' + $remoteWebRoot + '";' +
  ' MIRROR="' + $mirrorFlag + '";' +

  # ensure analysis dir exists
  ' mkdir -p "$WEBROOT/analysis" "$WEBROOT/static" "$WEBROOT/error";' +

  # FIX: create digest_latest.json alias if missing
  ' if [ ! -f "$STAGE/analysis/digest_latest.json" ]; then ' +
  '   for c in daily_digest_latest.json digest_view_model_latest.json daily_digest_view_model_latest.json digest_latest_view_model.json; do ' +
  '     if [ -f "$STAGE/analysis/$c" ]; then cp -af "$STAGE/analysis/$c" "$STAGE/analysis/digest_latest.json"; break; fi; ' +
  '   done; ' +
  ' fi;' +
  ' if [ ! -f "$STAGE/analysis/digest_latest.json" ]; then echo "{}" > "$STAGE/analysis/digest_latest.json"; fi;' +

  # copy static + analysis into webroot
  ' if [ -d "$STAGE/static" ]; then cp -af "$STAGE/static/." "$WEBROOT/static/"; fi;' +
  ' if [ -d "$STAGE/analysis" ]; then cp -af "$STAGE/analysis/." "$WEBROOT/analysis/"; fi;' +

  # optionally mirror some root files for convenience
  ' if [ "$MIRROR" = "1" ]; then ' +
  '   for f in index.html overlay.html sentiment.html digest.html app.css styles.css index.js; do ' +
  '     if [ -f "$STAGE/static/$f" ]; then cp -af "$STAGE/static/$f" "$WEBROOT/$f"; fi; ' +
  '   done; ' +
  ' fi;' +

  # stamp
  ' date > "$WEBROOT/deploy_stamp.txt"'

Run "remote publish" ($sshBase + @("bash","-lc",$publishCmd))

Ok "DEPLOY COMPLETE"
