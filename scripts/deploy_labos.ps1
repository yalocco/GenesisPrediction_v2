# scripts/deploy_labos.ps1
param(
    [string]$Profile = "dev"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path (Join-Path $PSScriptRoot "..")

. (Join-Path $ROOT "scripts/deploy_labos.config.ps1")

if (-not $DEPLOY_PROFILES.ContainsKey($Profile)) {
    throw "Profile not found: $Profile"
}

$cfg = $DEPLOY_PROFILES[$Profile]

$sshHost    = [string]$cfg.Host
$user       = [string]$cfg.User
$port       = [string]$cfg.Port
$key        = [string]$cfg.KeyPath
$localDir   = [string]$cfg.LocalDir
$remoteBase = [string]$cfg.RemoteBaseDir
$release    = [string]$cfg.RemoteReleaseName
$webroot    = "$remoteBase/public_html/$($cfg.WebRootDirName)"
$releaseDir = "$remoteBase/releases/$release"

Write-Host "[INFO] Deploy: $($cfg.Name) ($Profile)"
Write-Host "[INFO] Remote: ${user}@${sshHost}:${port}"
Write-Host "[INFO] ReleaseDir: $releaseDir"
Write-Host "[INFO] WebRoot   : $webroot"
Write-Host "[INFO] MirrorRootFiles: $($cfg.MirrorRootFiles)"

if (-not (Test-Path $localDir)) {
    throw "LocalDir not found: $localDir"
}
if (-not (Test-Path $key)) {
    throw "SSH key not found: $key"
}

$tmpTar = Join-Path $env:TEMP "labos_release.tar.gz"
if (Test-Path $tmpTar) {
    Remove-Item $tmpTar -Force
}

Write-Host "[INFO] tar create"
tar -czf $tmpTar -C $localDir .
if ($LASTEXITCODE -ne 0) {
    throw "tar create failed"
}

$sshArgs = @(
    "-i", $key,
    "-p", $port,
    "${user}@${sshHost}"
)

$scpArgs = @(
    "-i", $key,
    "-P", $port
)

function To-LF([string]$s) {
    return ($s -replace "`r", "")
}

function RunRemote([string]$script) {
    $script = To-LF $script

    $tmpLocal = Join-Path $env:TEMP ("labos_remote_" + [guid]::NewGuid().ToString() + ".sh")
    $tmpName = Split-Path $tmpLocal -Leaf
    $remoteTmp = "`$HOME/$tmpName"

    [System.IO.File]::WriteAllText($tmpLocal, $script, (New-Object System.Text.UTF8Encoding($false)))

    try {
        & scp @scpArgs $tmpLocal "${user}@${sshHost}:$remoteTmp"
        if ($LASTEXITCODE -ne 0) {
            throw "remote script upload failed"
        }

        & ssh @sshArgs "bash $remoteTmp"
        if ($LASTEXITCODE -ne 0) {
            throw "remote script execution failed"
        }

        & ssh @sshArgs "rm -f $remoteTmp" | Out-Null
    }
    finally {
        if (Test-Path $tmpLocal) {
            Remove-Item $tmpLocal -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "[INFO] remote mkdir"
RunRemote @"
set -e
mkdir -p "$remoteBase/releases"
mkdir -p "$releaseDir"
mkdir -p "$webroot"
mkdir -p "$webroot/static"
mkdir -p "$webroot/analysis"
mkdir -p "$webroot/data"
mkdir -p "$webroot/error"
"@

Write-Host "[INFO] scp upload (to HOME)"
& scp @scpArgs $tmpTar "${user}@${sshHost}:`$HOME/labos_release.tar.gz"
if ($LASTEXITCODE -ne 0) {
    throw "scp upload failed"
}

Write-Host "[INFO] remote move+extract"
RunRemote @"
set -e
mv "`$HOME/labos_release.tar.gz" "$releaseDir/release.tar.gz"
cd "$releaseDir"
tar -xzf release.tar.gz
rm -f release.tar.gz
"@

Write-Host "[INFO] remote publish"
RunRemote @"
set -e
mkdir -p "$webroot/static"
mkdir -p "$webroot/analysis"
mkdir -p "$webroot/data"
mkdir -p "$webroot/error"

if [ -d "$releaseDir/static" ]; then
  cp -af "$releaseDir/static/." "$webroot/static/"
fi

if [ -d "$releaseDir/analysis" ]; then
  cp -af "$releaseDir/analysis/." "$webroot/analysis/"
fi

if [ -d "$releaseDir/data" ]; then
  cp -af "$releaseDir/data/." "$webroot/data/"
fi

if [ "$($cfg.MirrorRootFiles)" = "True" ]; then
  for f in index.html overlay.html sentiment.html digest.html app.css styles.css index.js; do
    if [ -f "$releaseDir/static/`$f" ]; then
      cp -af "$releaseDir/static/`$f" "$webroot/`$f"
    fi
  done
fi

date > "$webroot/deploy_stamp.txt"
"@

Write-Host "[OK] DEPLOY COMPLETE"