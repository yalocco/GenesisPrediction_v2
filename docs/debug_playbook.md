はい、まさにその通りです 👍
**次に入れるべきは `debug_playbook.md` です。**

あなたの Repository Memory を見ると、

* 運用手順 → `runbook_morning.md` 
* 作業ルール → `working_agreement.md` 
* UI構造 → `ui_system.md` 
* パイプライン → `pipeline_system.md` 
* Repo構造 → `repo_map.md` 

ここまでは **設計・運用・思想**が揃っています。

しかしまだ一つ欠けています。

それが

```
トラブル時どう動くか
```

つまり **Debug Playbook** です。

---

# 役割の違い（重要）

### runbook_morning.md

通常運転

```
どうやって回すか
```

---

### debug_playbook.md

異常時

```
何が壊れたら
どこを見るか
どのコマンド
```

---

# GenesisPredictionに必要な理由

あなたのシステムは

```
scripts
↓
analysis
↓
UI
```

の責務分離構造です。 

つまりトラブルは必ず

1️⃣ scripts
2️⃣ analysis
3️⃣ UI

のどこかに分類できます。

これを **固定化した手順書**が `debug_playbook.md` です。

---

# docs/debug_playbook.md（完全版）

そのまま
**docs/debug_playbook.md**
として保存してください。

```md
# Debug Playbook (GenesisPrediction v2)

Status: Active
Purpose: Troubleshooting guide
Last Updated: 2026-03-06

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

**トラブルシューティング手順**

を固定化する。

目的

- AI / 人間が迷わない
- 原因切り分けを高速化
- スレ依存をなくす

---

# 1. 基本原則

GenesisPrediction の構造

```

scripts
↓
analysis
↓
UI

```

ルール

```

UIが壊れたら
まず analysis を見る

```

---

# 2. 一次切り分け

## UIがおかしい

例

```

数字が出ない
画像が出ない
ALL_ZERO

```

確認

```

data/world_politics/analysis

```

チェック

```

daily_news_latest.json
daily_summary_latest.json
sentiment_latest.json
health_latest.json

```

---

## Pipelineが止まる

確認

```

scripts/

```

実行ログ

```

run_daily_with_publish.ps1

```

典型エラー

```

missing raw news
missing dated json

```

---

## Morning Ritual失敗

実行

```

powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

```

ログ確認

```

=== step name ===

```

止まった step を確認。

---

# 3. よくあるエラー

## missing raw news

例

```

missing raw news:
data/world_politics/YYYY-MM-DD.json

```

原因

```

WorldDate mismatch

```

確認

```

data/world_politics/

```

---

## ALL_ZERO

例

```

positive 0
negative 0
neutral 0
mixed 0

```

原因

```

sentiment join mismatch

```

確認

```

sentiment_latest.json

```

---

## Overlay画像更新されない

確認

```

analysis/fx_overlay_latest.png

```

再生成

```

run_daily_fx_overlay.ps1

```

---

# 4. Debugコマンド

基本

```

git status
git diff
git pull

```

Morning Ritual

```

powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

```

FX

```

run_daily_fx_rates.ps1
run_daily_fx_inputs.ps1
run_daily_fx_overlay.ps1

```

Health

```

python scripts/build_data_health.py

```

---

# 5. 原則

トラブル時

```

GUIを疑う前に
analysisを確認する

```

GenesisPrediction の真実は

```

analysis/

```

である。

---

# 6. 最終判断

問題の分類

|症状|原因|
|---|---|
UI崩れ|UI|
数値なし|analysis|
pipeline停止|scripts|

---

END OF DOCUMENT
```
