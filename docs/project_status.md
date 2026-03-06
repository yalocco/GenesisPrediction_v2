できます 👍
あなたの `git tag` 出力を基に **`project_status.md` の完全版**を作りました。

あなたのプロジェクトの状態とも整合するように
**タグをカテゴリ整理して書いています。**

そのまま **docs/project_status.md を丸ごと置き換えてください。**

---

# docs/project_status.md（完全版）

```md
# Project Status (GenesisPrediction v2)
Status: Active
Last Updated: 2026-03-06

## 0. 目的
この1枚で「現在地」を復元できるようにする。

- スレ変更
- PC変更（会社 / 自宅）
- AI変更

が起きても、同じ前提から開発を再開できるようにする。

---

# 1. Current UI

Pages:

- Home: `app/static/index.html`
- Overlay: `app/static/overlay.html`
- Sentiment: `app/static/sentiment.html`
- Digest: `app/static/digest.html`

UI Baseline:

- `sentiment.html` baseline  
  （背景 / topbar / container / glass cards）

UI原則：

- UIは **analysis/（SST）だけを読む**
- UIで再計算しない
- UIは表示専用

---

# 2. Current Pipeline

Daily (Morning Ritual):

1. `git pull`（clean確認）

2. Main pipeline

```

scripts/run_daily_with_publish.ps1

```

目的：

- fetcher
- analyzer
- ViewModel生成
- analysis更新

3. FX lane

```

scripts/run_daily_fx_rates.ps1
scripts/run_daily_fx_inputs.ps1
scripts/run_daily_fx_overlay.ps1

```

生成：

- FX rate
- remittance calculation
- overlay PNG

4. Data Health

```

scripts/build_data_health.py

```

生成：

- health JSON

5. GUI確認

```

index.html
overlay.html
sentiment.html
digest.html

```

---

# 3. SST (Single Source of Truth)

GenesisPrediction v2 の真実は

```

analysis/

```

のみ。

- `analysis/` = 表示・判断の唯一の情報源
- `data/` = 素材
- `scripts/` = 生成装置
- `app/static/` = 表示

---

# 4. Git / Freeze Points

Branch

```

main

```

Known stable tags (freeze)

## UI

```

gui-mvp
gui-ui-stable-v1
gui-ui-stable-v1.1
gui-ui-stable-v2.0
gui-ui-stable-v2.1
ui-stable-pre-theme
ui-stable-2026-02-28
ui-stable-sentiment-v1

```

## Digest

```

digest-ui-ok-20260305

```

## Overlay / FX

```

overlay-stable-v1
fx-multi-overlay-v1

```

## Sentiment

```

sentiment-stable-v1
sentiment-thumb-step1

```

## Morning Ritual / Pipeline research

```

research-morning-ritual-v1
research-morning-ritual-stable-v2
research-morning-ritual-stable-v3

```

## Prediction / Trend research

```

research-prediction-persistence-v1
research-trend3-fx-v1
research-trend3-fx-v2B-stable

```

## Reports

```

research-reports-stable-v1

```

## Deploy

```

deploy-ready-v1

```

---

# 5. Known Issues (if any)

現在の既知問題

- Sentiment KPI が `unknown` になるケースあり
- Sentiment分類（positive / negative / neutral / mixed）が未反映
- join mismatch の可能性

---

# 6. Next Action (one)

現在の作業

```

Sentiment分類の有効化
positive / negative / neutral / mixed

```

対象

```

sentiment pipeline
sentiment UI

```

---

# 7. Rules (short)

基本ルール

```

1ターン = 1作業
差分提案禁止（完全ファイルのみ）
GUIファイルはダウンロード運用

```

---

# 8. Knowledge System

GenesisPrediction v2 の知識構造

```

Chat Memory
↓
Repository Memory (docs)
↓
Project Knowledge

```

Repository Memory

```

docs/ui_system.md
docs/pipeline_system.md
docs/chat_operating_rules.md
docs/genesis_brain.md
docs/project_status.md

```

---

GenesisPrediction v2 は  
**AIと人間の共同開発プロジェクト**である。
```
