param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$RemotePath = "/home/c3999143/public_html/labos.soma-samui.com",
    [string]$HostName = "www143.conoha.ne.jp",
    [string]$UserName = "c3999143",
    [int]$Port = 8022,
    [string]$KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem"
)

$ErrorActionPreference = "Stop"

$PayloadDir = Join-Path $Root "dist\labos_deploy"
$TarPath = Join-Path $Root "dist\labos_deploy.tar.gz"

$RemoteTarget = "${UserName}@${HostName}"
$RemoteTarName = "labos_deploy.tar.gz"
$RemoteTarPath = "$RemotePath/$RemoteTarName"

Write-Host "[deploy] START"

# -------------------------
# TAR
# -------------------------
if (Test-Path $TarPath) {
    Remove-Item $TarPath -Force
}

tar -czf $TarPath -C $PayloadDir .

# -------------------------
# REMOTE PREP
# -------------------------
ssh -i $KeyPath -p $Port $RemoteTarget "mkdir -p $RemotePath && rm -f $RemoteTarPath"

# -------------------------
# UPLOAD
# -------------------------
scp -i $KeyPath -P $Port $TarPath "${RemoteTarget}:${RemoteTarPath}"

# -------------------------
# DEPLOY（1行コマンド）
# -------------------------
$cmd = "cd $RemotePath; tar -xzf $RemoteTarName -C $RemotePath; rm -f $RemoteTarName"

ssh -i $KeyPath -p $Port $RemoteTarget $cmd

Write-Host "[deploy] DONE"