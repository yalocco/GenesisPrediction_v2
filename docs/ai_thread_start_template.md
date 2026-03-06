了解です、相棒 👍
では **新スレ用 `ai_thread_start_template.md` の最新版**を出します。

今回は増えた分として、少なくとも次を反映します。

* `docs/analysis_data_schema.md`
* `docs/prediction_architecture.md`
* `docs/genesis_prediction_roadmap.md`

`labos_business_model.md` は前に話した通り **必須情報源ではない**ので、
今回は **通常テンプレからは外し、必要時のみ読む Optional 扱い** にしておくのが一番安全です。

---

# docs/ai_thread_start_template.md（完全版）

これで **丸ごと上書き**してください。

```md
# GenesisPrediction v2 — AI Thread Start

このプロジェクトでは  
**Repository Memory（docs/）を AI の情報源として使用します。**

AIはまず以下を読み、プロジェクトの前提を復元してください。

---

# Repository Memory

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

# Important Principles

GenesisPrediction v2 の設計原則

SST (Single Source of Truth)

```

analysis/

```

rules

```

scripts → analysis を生成
analysis → UIが読む
UI → 再計算しない

```

---

# Development Rules

```

1ターン = 1作業
差分修正禁止
完全ファイル提示
GUIはダウンロード運用

```

---

# Pipeline Overview

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
GUI確認

```

---

# Current Task

（ここに当該スレの目的を書く）

例

```

Sentiment分類 有効化
positive / negative / neutral / mixed

```

---

# Current State

（ここに現在の状況を書く）

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

# Next Action

（次の1手）

例

```

sentiment_latest.json の確認

```

---

END
```
