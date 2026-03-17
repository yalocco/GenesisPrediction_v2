param(
    [string]$Profile = "dev"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===================================="
Write-Host "GenesisPrediction LABOS Deploy"
Write-Host "===================================="

$ROOT = Resolve-Path (Join-Path $PSScriptRoot "..")
Write-Host "ROOT    : $ROOT"
Write-Host "PROFILE : $Profile"

function Write-LfTextFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $normalized = $Content -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $normalized, $utf8NoBom)
}

# ------------------------------------------------------------
# config load
# ------------------------------------------------------------
$configPath = Join-Path $PSScriptRoot "deploy_labos.config.ps1"

if (-not (Test-Path -LiteralPath $configPath)) {
    throw "deploy_labos.config.ps1 not found"
}

. $configPath

if (-not (Get-Variable -Name DEPLOY_PROFILES -ErrorAction SilentlyContinue)) {
    throw "DEPLOY_PROFILES not found in deploy_labos.config.ps1"
}

if (-not $DEPLOY_PROFILES.ContainsKey($Profile)) {
    throw "profile not found: $Profile"
}

$cfg = $DEPLOY_PROFILES[$Profile]

$DeployName        = [string]$cfg.Name
$RemoteHost        = [string]$cfg.Host
$RemoteUser        = [string]$cfg.User
$RemotePort        = [string]$cfg.Port
$KeyPath           = [string]$cfg.KeyPath
$LocalDir          = [string]$cfg.LocalDir
$RemoteBaseDir     = [string]$cfg.RemoteBaseDir
$RemoteReleaseName = [string]$cfg.RemoteReleaseName
$WebRootDirName    = [string]$cfg.WebRootDirName
$MirrorRootFiles   = [bool]$cfg.MirrorRootFiles

if ([string]::IsNullOrWhiteSpace($RemoteHost))        { throw "Host is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($RemoteUser))        { throw "User is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($RemotePort))        { throw "Port is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($KeyPath))           { throw "KeyPath is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($LocalDir))          { throw "LocalDir is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($RemoteBaseDir))     { throw "RemoteBaseDir is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($RemoteReleaseName)) { throw "RemoteReleaseName is missing in profile '$Profile'" }
if ([string]::IsNullOrWhiteSpace($WebRootDirName))    { throw "WebRootDirName is missing in profile '$Profile'" }

if (-not (Test-Path -LiteralPath $KeyPath)) {
    throw "SSH key not found: $KeyPath"
}

if (-not (Test-Path -LiteralPath $LocalDir)) {
    throw "Local deploy payload not found: $LocalDir"
}

$ReleaseDir = "$RemoteBaseDir/releases/$RemoteReleaseName"
$WebRoot    = "$RemoteBaseDir/public_html/$WebRootDirName"

Write-Host ""
Write-Host "[INFO] Deploy: $DeployName ($Profile)"
Write-Host "[INFO] Remote: ${RemoteUser}@${RemoteHost}:${RemotePort}"
Write-Host "[INFO] ReleaseDir: $ReleaseDir"
Write-Host "[INFO] WebRoot   : $WebRoot"
Write-Host "[INFO] MirrorRootFiles: $MirrorRootFiles"

# ------------------------------------------------------------
# temp files
# ------------------------------------------------------------
$TarPath   = Join-Path $env:TEMP "labos_release.tar.gz"
$RemoteTar = "/tmp/labos_release.tar.gz"

$RemoteScriptUpload  = "/home/$RemoteUser/labos_remote_upload_$RemoteReleaseName.sh"
$RemoteScriptExtract = "/home/$RemoteUser/labos_remote_extract_$RemoteReleaseName.sh"
$RemoteScriptPublish = "/home/$RemoteUser/labos_remote_publish_$RemoteReleaseName.sh"

$LocalScriptUpload  = Join-Path $env:TEMP "labos_remote_upload_$RemoteReleaseName.sh"
$LocalScriptExtract = Join-Path $env:TEMP "labos_remote_extract_$RemoteReleaseName.sh"
$LocalScriptPublish = Join-Path $env:TEMP "labos_remote_publish_$RemoteReleaseName.sh"

# ------------------------------------------------------------
# tar create
# ------------------------------------------------------------
Write-Host "[INFO] tar create"

if (Test-Path -LiteralPath $TarPath) {
    Remove-Item -LiteralPath $TarPath -Force
}

tar -czf $TarPath -C $LocalDir .
if ($LASTEXITCODE -ne 0) {
    throw "tar create failed"
}

# ------------------------------------------------------------
# remote scripts (LF only)
# ------------------------------------------------------------
$uploadScript = @"
#!/bin/bash
set -e
mkdir -p "$RemoteBaseDir/releases"
"@

$extractScript = @"
#!/bin/bash
set -e
mkdir -p "$ReleaseDir"
tar -xzf "$RemoteTar" -C "$ReleaseDir"
"@

$publishScript = @"
#!/bin/bash
set -e

if [ ! -d "$WebRoot" ]; then
  echo "[REMOTE] web root not found: $WebRoot"
  exit 1
fi

if [ "$MirrorRootFiles" = "True" ] || [ "$MirrorRootFiles" = "true" ]; then
  find "$WebRoot" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "$ReleaseDir"/. "$WebRoot"/
else
  find "$WebRoot" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "$ReleaseDir"/. "$WebRoot"/
fi
"@

Write-LfTextFile -Path $LocalScriptUpload  -Content $uploadScript
Write-LfTextFile -Path $LocalScriptExtract -Content $extractScript
Write-LfTextFile -Path $LocalScriptPublish -Content $publishScript

# ------------------------------------------------------------
# remote mkdir
# ------------------------------------------------------------
Write-Host "[INFO] remote mkdir"

scp -i $KeyPath -P $RemotePort `
    $LocalScriptUpload `
    "${RemoteUser}@${RemoteHost}:${RemoteScriptUpload}"

if ($LASTEXITCODE -ne 0) {
    throw "remote script upload failed"
}

ssh -i $KeyPath -p $RemotePort `
    "${RemoteUser}@${RemoteHost}" `
    "bash $RemoteScriptUpload"

if ($LASTEXITCODE -ne 0) {
    throw "remote mkdir failed"
}

# ------------------------------------------------------------
# scp upload
# ------------------------------------------------------------
Write-Host "[INFO] scp upload (to HOME)"

scp -i $KeyPath -P $RemotePort `
    $TarPath `
    "${RemoteUser}@${RemoteHost}:${RemoteTar}"

if ($LASTEXITCODE -ne 0) {
    throw "payload upload failed"
}

# ------------------------------------------------------------
# remote move+extract
# ------------------------------------------------------------
Write-Host "[INFO] remote move+extract"

scp -i $KeyPath -P $RemotePort `
    $LocalScriptExtract `
    "${RemoteUser}@${RemoteHost}:${RemoteScriptExtract}"

if ($LASTEXITCODE -ne 0) {
    throw "remote extract script upload failed"
}

ssh -i $KeyPath -p $RemotePort `
    "${RemoteUser}@${RemoteHost}" `
    "bash $RemoteScriptExtract"

if ($LASTEXITCODE -ne 0) {
    throw "remote extract failed"
}

# ------------------------------------------------------------
# remote publish
# ------------------------------------------------------------
Write-Host "[INFO] remote publish"

scp -i $KeyPath -P $RemotePort `
    $LocalScriptPublish `
    "${RemoteUser}@${RemoteHost}:${RemoteScriptPublish}"

if ($LASTEXITCODE -ne 0) {
    throw "remote publish script upload failed"
}

ssh -i $KeyPath -p $RemotePort `
    "${RemoteUser}@${RemoteHost}" `
    "bash $RemoteScriptPublish"

if ($LASTEXITCODE -ne 0) {
    throw "remote publish failed"
}

# ------------------------------------------------------------
# cleanup
# ------------------------------------------------------------
ssh -i $KeyPath -p $RemotePort `
    "${RemoteUser}@${RemoteHost}" `
    "rm -f $RemoteScriptUpload $RemoteScriptExtract $RemoteScriptPublish $RemoteTar" | Out-Null

Remove-Item -LiteralPath $TarPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $LocalScriptUpload -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $LocalScriptExtract -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $LocalScriptPublish -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "[OK] DEPLOY COMPLETE"
Write-Host ""