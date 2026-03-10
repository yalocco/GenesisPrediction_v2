# GenesisPrediction v2 — AI Thread Start Template

Purpose  
このテンプレートは、新しいAI作業スレを開始する際に使用する。  
AIはこの内容を読み、GenesisPrediction v2 の構造・ルール・現在状態を復元する。

---

# Repository Memory

AIはまず以下のドキュメントを読み、プロジェクト前提を理解する。

## Core Architecture

docs/repo_map.md  
docs/pipeline_system.md  
docs/ui_system.md  
docs/ui_data_dependencies.md  
docs/analysis_data_schema.md  
docs/prediction_architecture.md  
docs/genesis_prediction_roadmap.md  

---

## Project Philosophy

docs/genesis_brain.md  

---

## Operation

docs/runbook_morning.md  

---

## Debug

docs/debug_playbook.md  

---

## Development Rules

docs/working_agreement.md  
docs/chat_operating_rules.md  
docs/gui_phase2_working_rules.md  

---

## Project Status

docs/project_status.md  

---

## System Memory

docs/system_history.md  
docs/decision_log.md  

---

## Optional (LABOS / Business)

必要時のみ参照

docs/labos_business_model.md  

---

# Core Architecture Principles

GenesisPrediction v2 の設計原則

Single Source of Truth

```

analysis/

```

データ責務

```

scripts → analysis を生成
analysis → UIが読む
UI → 再計算しない

```

重要原則

```

analysis = 唯一の真実
UIはanalysisを読むだけ
scriptsはUIを知らない

```

---

# Development Rules

AIと人間の共同作業ルール

```

1ターン = 1作業
差分修正禁止
完全ファイル提示
大きなファイルはダウンロード運用
GUIは安全運用

```

特に

```

app/static

```

のGUIファイルは事故防止のため慎重に扱う。

---

# Pipeline Overview

GenesisPrediction v2 の日次処理

Morning Ritual

```

git pull
↓
run_daily_with_publish
↓
FX lane
↓
build_data_health
↓
latest artifacts refresh
↓
GUI確認

```

---

# Known Facts (確定情報)

AIが誤解してはいけない前提

```

analysis = Single Source of Truth
UI = read-only layer
Digest = data/digest/view_model_latest.json
Sentiment = analysis/world_politics/sentiment_latest.json

```

さらに

```

data → 素材
scripts → 生成
analysis → 真実
UI → 表示

```

---

# Current Thread Task

（このスレで行う作業目的を書く）

例

```

Sentiment分類 有効化
positive / negative / neutral / mixed

```

---

# Current State

（現在の状況を書く）

例

```

Digest KPI

positive 0
negative 0
neutral 0
mixed 0
unknown 49

```

---

# Known Issues

（既知の問題を書く）

例

```

Sentiment classification 未適用
unknown が多い

```

---

# Next Action

（次の1手）

例

```

sentiment_latest.json の構造確認

```

---

# AI Instructions

AIは以下を守ること

```

analysis を最優先で確認
UIで再計算しない
推測ではなくデータを確認する

```

また

```

大きなファイル（200行以上）は
ダウンロード方式で提示する

```

---

# Thread End Rule

スレ終了時

```

commit
push
repo clean

```

を確認する。

---

END
```
