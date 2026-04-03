param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$RemotePath = "/home/c3999143/public_html/labos.soma-samui.com",
    [string]$HostName = "www143.conoha.ne.jp",
    [string]$UserName = "c3999143",
    [int]$Port = 8022,
    [string]$KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Log($msg) {
    Write-Host "[deploy] $msg"
}

function Fail($msg) {
    throw $msg
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $false)]
        [string[]]$ArgumentList = @(),

        [Parameter(Mandatory = $false)]
        [switch]$AllowFailure
    )

    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE

    if (-not $AllowFailure -and $exitCode -ne 0) {
        Fail "Command failed (exit=$exitCode): $FilePath $($ArgumentList -join ' ')"
    }

    return $exitCode
}

$PayloadDir = Join-Path $Root "dist\labos_deploy"
$TarPath = Join-Path $Root "dist\labos_deploy.tar.gz"

if (!(Test-Path $PayloadDir)) {
    Fail "Payload directory not found: $PayloadDir"
}

if (!(Test-Path $KeyPath)) {
    Fail "SSH key not found: $KeyPath"
}

$RemoteTarget = "${UserName}@${HostName}"
$RemoteTarName = ".deploy_labos_payload.tar.gz"
$RemoteTarPath = "$RemotePath/$RemoteTarName"

Log "START"
Log "ROOT           : $Root"
Log "PAYLOAD        : $PayloadDir"
Log "REMOTE TARGET  : $RemoteTarget"
Log "REMOTE PATH    : $RemotePath"
Log "MODE           : $(if ($DryRun) { 'DRY RUN' } else { 'LIVE' })"
Log "SCOPE          : target hierarchy only"

if (Test-Path $TarPath) {
    Remove-Item $TarPath -Force
}

Log "Pack payload tar.gz"
Invoke-Native -FilePath "tar" -ArgumentList @("-czf", $TarPath, "-C", $PayloadDir, ".")
Log "TAR READY      : $TarPath"

$remotePrepare = @"
set -e
mkdir -p '$RemotePath'
rm -f '$RemoteTarPath'
"@

$remoteDeploy = @"
set -e
mkdir -p '$RemotePath'
find '$RemotePath' -mindepth 1 -maxdepth 1 ! -name '$RemoteTarName' -exec rm -rf {} +
tar -xzf '$RemoteTarPath' -C '$RemotePath'
rm -f '$RemoteTarPath'
"@

if ($DryRun) {
    Log "DRY RUN remote prepare script:"
    Write-Host $remotePrepare
    Log "DRY RUN upload destination: $RemoteTarPath"
    Log "DRY RUN remote deploy script:"
    Write-Host $remoteDeploy
    Log "DONE (DRY RUN)"
    exit 0
}

Log "Ensure target directory exists and remove previous temp tar"
Invoke-Native -FilePath "ssh" -ArgumentList @("-i", $KeyPath, "-p", "$Port", $RemoteTarget, $remotePrepare)

Log "Upload tar into target hierarchy only"
Invoke-Native -FilePath "scp" -ArgumentList @("-i", $KeyPath, "-P", "$Port", $TarPath, "${RemoteTarget}:${RemoteTarPath}")

Log "Full replacement inside target hierarchy only"
Invoke-Native -FilePath "ssh" -ArgumentList @("-i", $KeyPath, "-p", "$Port", $RemoteTarget, $remoteDeploy)

Log "DONE"
