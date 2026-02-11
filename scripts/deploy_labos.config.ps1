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

    # 🔑 あなたの実在する鍵パス（変更しないでOKならこのまま）
    KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem"

    # ローカルビルド成果物
    LocalDir = "D:\AI\Projects\GenesisPrediction_v2\dist\labos_deploy"

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

    Host = "www143.conoha.ne.jp"
    User = "c3999143"
    Port = "8022"

    KeyPath = "D:\AI\Projects\keys\genesisprediction-labos.pem"

    LocalDir = "D:\AI\Projects\GenesisPrediction_v2\dist\labos_deploy"

    RemoteBaseDir = "/home/c3999143"

    RemoteReleaseName = "prod_$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    WebRootDirName = "labos.soma-samui.com"

    MirrorRootFiles = $true
  }
}
