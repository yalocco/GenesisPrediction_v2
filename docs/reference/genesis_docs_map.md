# Genesis Docs Map
GenesisPrediction v2

Status: Active  
Purpose: docs/ フォルダ全体の構造と読む順番を定義する  
Last Updated: 2026-03-09

---

# 0. Purpose

このドキュメントは

```

docs/

```

フォルダの **公式地図（Docs Map）** である。

目的

- docs の構造を固定する
- AIが読む順番を明確にする
- 新しいAI / 新しいチャット / RAG環境で迷子にならないようにする
- Repository Memory を体系化する

---

# 1. Docs Architecture

GenesisPrediction の docs は  
以下の階層構造で整理される。

```

BOOTSTRAP
↓
ENTRY
↓
ARCHITECTURE
↓
OPERATION
↓
SYSTEM STATE
↓
VISION

```

---

# 2. BOOTSTRAP

AIが最初に読むドキュメント。

```

AI_PROJECT_BOOTSTRAP.md

```

役割

- プロジェクトの目的
- システムの基本構造
- SST原則
- Daily Operation
- Repository Memory入口

新しいAIはまずこのファイルを読む。

---

# 3. ENTRY

Repository Memory の入口。

```

ai_quick_context.md
repository_memory_index.md

```

役割

### ai_quick_context.md

短時間でプロジェクトを理解するための概要。

内容

```

目的
基本構造
SST
主要コンポーネント

```

---

### repository_memory_index.md

docs 全体の索引。

役割

```

どのドキュメントが何を説明するか

```

を示す。

---

# 4. ARCHITECTURE

システム設計。

```

repo_map.md
pipeline_system.md
analysis_data_schema.md
prediction_architecture.md
ui_system.md
ui_data_dependencies.md

```

役割

### repo_map.md

Repository の構造説明。

### pipeline_system.md

データ処理パイプライン。

```

fetch
analyze
aggregate
publish

```

---

### analysis_data_schema.md

SSTデータ構造。

```

analysis/

```

配下の JSON schema を定義する。

---

### prediction_architecture.md

Prediction Engine の基本構造。

---

### ui_system.md

UIアーキテクチャ。

```

index
overlay
sentiment
digest
prediction
prediction_history

```

---

### ui_data_dependencies.md

UIが参照するデータ一覧。

---

# 5. OPERATION

運用ルール。

```

runbook_morning.md
debug_playbook.md
working_agreement.md
chat_operating_rules.md
ai_rules.md

```

---

### runbook_morning.md

Daily Operation。

```

Morning Ritual

```

の公式手順。

---

### debug_playbook.md

デバッグ手順。

---

### working_agreement.md

開発ルール。

重要ルール

```

1ターン = 1作業
差分禁止
完全ファイル

```

---

### chat_operating_rules.md

チャット運用ルール。

---

### ai_rules.md

AI共同開発ルール。

---

# 6. SYSTEM STATE

プロジェクトの状態。

```

project_status.md
system_history.md
decision_log.md

```

---

### project_status.md

現在のシステム状態。

---

### system_history.md

システム進化履歴。

---

### decision_log.md

重要な設計判断の記録。

---

# 7. VISION

長期思想。

```

genesis_prediction_roadmap.md
genesis_brain.md
prediction_layer_design_principles.md

```

---

### genesis_prediction_roadmap.md

長期開発ロードマップ。

---

### genesis_brain.md

GenesisPrediction の思想。

```

Observation
↓
Meaning
↓
Prediction

```

---

### prediction_layer_design_principles.md

Prediction Layer 設計原則。

```

Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction

```

---

# 8. AI Reading Order

AIが理解するための推奨順序。

```

1 AI_PROJECT_BOOTSTRAP.md
2 ai_quick_context.md
3 repository_memory_index.md
4 repo_map.md
5 pipeline_system.md
6 project_status.md
7 runbook_morning.md

```

この順序で

```

目的
構造
現在状態
運用

```

を理解できる。

---

# 9. Single Source of Truth

GenesisPrediction の真実は

```

analysis/

```

である。

役割

```

data       = 素材
scripts    = 生成
analysis   = SST
UI         = 表示
docs       = 知識

```

---

# 10. Docs Philosophy

docs の目的は

```

迷いを消すこと

```

である。

設計

```

構造を固定
↓
ルールを固定
↓
判断を簡単にする

```

---

# 11. Maintenance Rule

docs 更新時のルール。

```

構造変更があった場合

genesis_docs_map.md
repository_memory_index.md

を更新する

```

---

# 12. Final Principle

GenesisPrediction の docs は

```

Human + AI

```

が共同で理解できる形で管理する。

docs は

```

AI Memory

```

である。

---

END OF DOCUMENT
```
