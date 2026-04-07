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

function Normalize-RemotePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $normalized = [string]$Path
    $normalized = $normalized -replace "`r", ""
    $normalized = $normalized -replace "`n", ""
    $normalized = $normalized.Trim()

    if ([string]::IsNullOrWhiteSpace($normalized)) {
        Fail "RemotePath is empty after normalization."
    }

    if ($normalized -ne "/") {
        $normalized = $normalized.TrimEnd("/")
    }

    return $normalized
}

function Normalize-UnixScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $normalized = [string]$Text
    $normalized = $normalized -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    $normalized = $normalized.Trim()

    if ([string]::IsNullOrWhiteSpace($normalized)) {
        Fail "Remote shell script is empty after normalization."
    }

    return $normalized + "`n"
}

function Quote-ShellSingle {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $escaped = $Text -replace "'", "''"
    return "'" + $escaped + "'"
}

$PayloadDir = Join-Path $Root "dist\labos_deploy"
$TarPath = Join-Path $Root "dist\labos_deploy.tar.gz"

if (!(Test-Path $PayloadDir)) {
    Fail "Payload directory not found: $PayloadDir"
}

if (!(Test-Path $KeyPath)) {
    Fail "SSH key not found: $KeyPath"
}

$RemotePath = Normalize-RemotePath -Path $RemotePath
$RemoteTarget = "${UserName}@${HostName}"
$RemoteTarName = ".deploy_labos_payload.tar.gz"
$RemoteTarPath = "$RemotePath/$RemoteTarName"

$QuotedRemotePath = Quote-ShellSingle -Text $RemotePath
$QuotedRemoteTarPath = Quote-ShellSingle -Text $RemoteTarPath
$QuotedRemoteTarName = Quote-ShellSingle -Text $RemoteTarName

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

$remotePrepare = Normalize-UnixScript @"
set -e
mkdir -p $QuotedRemotePath
rm -f $QuotedRemoteTarPath
"@

$remoteDeploy = Normalize-UnixScript @"
set -e
mkdir -p $QuotedRemotePath
find $QuotedRemotePath -mindepth 1 -maxdepth 1 ! -name $QuotedRemoteTarName -exec rm -rf {} +
tar -xzf $QuotedRemoteTarPath -C $QuotedRemotePath
rm -f $QuotedRemoteTarPath
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
