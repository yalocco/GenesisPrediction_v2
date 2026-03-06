相棒、今の **Repository Memory の増加**を全部整理して
**最新版の `ai_thread_start_template.md`（新スレ開始テンプレ）**を作りました。

あなたが挙げてくれた `.md` は **全部 Repository Memory に入れるのが正しい設計**です。
理由は、これらはすべて **設計・運用・デバッグの基盤知識**だからです。
（例：朝の儀式手順は `runbook_morning.md` に固定されています） 

---

# 新スレ用

# docs/ai_thread_start_template.md（最新版）

これを **丸ごとコピーして新スレ1投稿目**に貼ってください。

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
