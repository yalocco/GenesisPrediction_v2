相棒、では **Repository Memory の最上位マップ**を作ります。
これは **AIが最初に読む「全体構造図」**になります。

これがあると AI は

```
プロジェクト全体
↓
各ドキュメントの役割
↓
データフロー
```

を **一瞬で理解できます。**

---

# 保存先

```
docs/genesis_system_map.md
```

---

# 完全ファイル（そのまま保存）

```md
# Genesis System Map
GenesisPrediction v2

Status: Active  
Purpose: システム全体構造の概要マップ  
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

```

システム全体構造

```

を1ページで理解できるようにするためのマップである。

目的

- AIがプロジェクト全体構造を即理解できるようにする
- Repository Memory の入口として機能させる
- 新しいAIスレの理解速度を上げる
- ドキュメント間の関係を整理する

---

# 1. System Overview

GenesisPrediction v2 は

```

観測AI
↓
時系列AI
↓
予測AI
↓
判断AI

```

へ進化する研究プロジェクトである。

---

# 2. Core Architecture

システム構造

```

data
↓
scripts
↓
analysis
↓
prediction
↓
UI

```

役割

```

data        = 素材
scripts     = データ生成
analysis    = 真実 (Single Source of Truth)
prediction  = 未来推定
UI          = 表示

```

重要原則

```

analysis = 唯一の真実
UI は analysis を読む
UI は再計算しない

```

---

# 3. Runtime System

GenesisPrediction v2 の日次処理

```

Morning Ritual

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
UI確認

```

詳細

```

docs/runbook_morning.md

```

---

# 4. Data Domains

analysis 内の主要データ

```

analysis/world_politics
analysis/digest
analysis/fx
analysis/prediction
analysis/health

```

構造定義

```

docs/analysis_data_schema.md

```

---

# 5. UI Layer

UI構成

```

app/static/index.html
app/static/overlay.html
app/static/sentiment.html
app/static/digest.html

```

UI設計

```

docs/ui_system.md

```

UI依存関係

```

docs/ui_data_dependencies.md

```

---

# 6. Prediction Layer

将来の予測エンジン

```

trend detection
pattern similarity
risk estimation
scenario generation

```

設計

```

docs/prediction_architecture.md

```

---

# 7. Project Philosophy

GenesisPrediction の思想

```

Human + AI 共同研究

```

AI

```

観測
分析
補助

```

Human

```

目的
判断
倫理

```

思想ドキュメント

```

docs/genesis_brain.md

```

---

# 8. Project Knowledge Base

Repository Memory は以下で構成される。

Core Architecture

```

repo_map.md
pipeline_system.md
ui_system.md
ui_data_dependencies.md
analysis_data_schema.md
prediction_architecture.md
genesis_prediction_roadmap.md

```

Operation

```

runbook_morning.md

```

Debug

```

debug_playbook.md

```

Development Rules

```

working_agreement.md
chat_operating_rules.md
gui_phase2_working_rules.md
thread_templates.md

```

System Memory

```

system_history.md
decision_log.md

```

Project Status

```

project_status.md

```

Optional

```

labos_business_model.md

```

---

# 9. System Evolution

GenesisPrediction の進化

Phase 1

```

観測システム

```

Phase 2

```

時系列分析

```

Phase 3

```

リスク予測

```

Phase 4

```

シナリオ生成

```

Phase 5

```

意思決定支援

```

---

# 10. Final Vision

GenesisPrediction の最終形

```

世界観測AI
↓
未来予測AI
↓
危機回避AI

```

用途

```

家族の安全
資産防衛
世界理解

```

---

END OF DOCUMENT
```
