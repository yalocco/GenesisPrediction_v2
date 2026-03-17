# DEPLOY_LABOS_RUNBOOK
GenesisPrediction v2 / LABOS Deploy（HARDENED Phase2）

---

## ■ 目的

LABOS deploy を

「動く」から
「壊れない」

へ進化させる

---

## ■ 原則

- deploy は **必ず再実行可能**
- payload は **自己完結**
- 不完全な状態では **絶対に実行しない**
- root は **毎回完全再構築**
- 人間は **1コマンドのみ実行**

---

## ■ 実行コマンド（唯一）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1
````

DryRun:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1 -DryRun
```

---

## ■ 処理フロー（内部）

```plaintext
run_deploy_labos.ps1
↓
build_labos_deploy_payload.ps1
↓
deploy_labos.ps1
↓
verify
```

---

## ■ Phase2 Hardening 内容

### 1. Payload 完全化

* `.htaccess` を payload に必須同梱
* `/static`
* `/data`
* `/analysis`
* manifest.json

### 2. Build 時チェック

* 必須ファイル欠損 → 即停止
* prediction_latest 必須
* history_index 必須

### 3. Deploy 前チェック

* manifest 存在確認
* root ファイル存在確認

### 4. Remote Deploy

* current → backup に退避
* payload 展開
* root ファイル検証

### 5. Verify

* `.htaccess` 存在確認
* prediction_latest 存在確認

---

## ■ 必須ファイル（root）

* `.htaccess`

---

## ■ 必須データ

* `data/prediction/prediction_latest.json`
* `data/prediction/prediction_history_index.json`

---

## ■ ディレクトリ構成（deploy後）

```plaintext
current/
  ├── .htaccess
  ├── static/
  ├── data/
  ├── analysis/
  └── manifest.json
```

---

## ■ Rollback 手順

```bash
cd /home/USERNAME/labos_root

rm -rf current
mv backup current
```

---

## ■ 失敗時の判断

### build 失敗

→ データ生成が壊れている
→ Prediction / FX / analysis を確認

### deploy 失敗

→ 通信 or 権限問題

### verify 失敗

→ payload 不完全
→ build に問題あり

---

## ■ 禁止事項

* build を飛ばして deploy
* deploy を単体実行
* root を手動修正
* server 上で直接修正

---

## ■ 運用ルール

* deploy は必ず自宅PC
* deploy 前に git clean 確認
* Morning Ritual 完走後に実行

---

## ■ Definition of Done

* deploy が毎回同じ結果になる
* root 消失事故が発生しない
* 失敗しても復旧できる
* run スクリプト1発で完結

---

## ■ 最終状態

LABOS deploy は

「作業」ではなく
「安全な儀式」である

````
