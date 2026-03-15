# scripts/deploy_labos.config.ps1
# ------------------------------------------------------------
# GenesisPrediction LABOS deploy config (ConoHa WING)
# ------------------------------------------------------------
# SSH:
#   Host  : www143.conoha.ne.jp
#   User  : c3999143
#   Port  : 8022
#
# Web root for subdomain:
#   /home/c3999143/public_html/labos.soma-samui.com
#
# Deploy strategy:
#   - Upload to staging:   $HOME/releases/<name>
#   - Publish to webroot:  public_html/labos.soma-samui.com
# ------------------------------------------------------------

Set-StrictMode -Version Latest

$DEPLOY_PROFILES = @{

  "dev" = @{
    Name = "LABOS DEV"

    # SSH
    Host = "www143.conoha.ne.jp"
    User = "c3999143"
    Port = "8022"

    # SSH private key
    KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem"

    # ローカル deploy 元
    # build_labos_deploy_payload.ps1 の出力先に合わせる
    LocalDir = "D:\AI\Projects\GenesisPrediction_v2\dist\labos_payload"

    # サーバー側 HOME
    RemoteBaseDir = "/home/c3999143"

    # staging release name
    RemoteReleaseName = "dev_$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    # 公開先サブドメインディレクトリ
    WebRootDirName = "labos.soma-samui.com"

    # ルート互換ファイルをミラーするか
    MirrorRootFiles = $true
  }

  "prod" = @{
    Name = "LABOS PROD"

    # SSH
    Host = "www143.conoha.ne.jp"
    User = "c3999143"
    Port = "8022"

    # SSH private key
    KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem"

    # ローカル deploy 元
    # build_labos_deploy_payload.ps1 の出力先に合わせる
    LocalDir = "D:\AI\Projects\GenesisPrediction_v2\dist\labos_payload"

    # サーバー側 HOME
    RemoteBaseDir = "/home/c3999143"

    # staging release name
    RemoteReleaseName = "prod_$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    # 公開先サブドメインディレクトリ
    WebRootDirName = "labos.soma-samui.com"

    # ルート互換ファイルをミラーするか
    MirrorRootFiles = $true
  }
}