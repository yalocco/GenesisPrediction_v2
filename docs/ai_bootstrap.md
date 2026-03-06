了解しました。
**AI Bootstrap 設計**として、`docs/ai_bootstrap.md` の**完全ファイル**を作ります。
これは **「新しいAIが最初に読む起動スクリプト」**です。

既にある Repository Memory の構造（`repository_memory_index.md` → system map → 各ドキュメント）を利用します。

つまり役割はこれです。

```
AI 起動
↓
ai_bootstrap.md
↓
Repository Memory 読み込み
↓
システム理解
↓
作業開始
```

---

# 保存先

```
docs/ai_bootstrap.md
```

---

# docs/ai_bootstrap.md（完全ファイル）

```md
# AI Bootstrap
GenesisPrediction v2

Status: Active
Purpose: 新しいAIがGenesisPredictionを起動時に理解するための最初のドキュメント
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```

AI起動プロトコル

```

である。

新しいAIはまずこのドキュメントを読み、

```

GenesisPrediction v2

```

の構造を理解する。

用途

```

新しいAIスレ
新しいAIモデル
Open-WebUI
ローカルLLM
ChatGPT

```

すべて同じ起動手順を使用する。

---

# 1. Project Overview

GenesisPrediction v2 は

```

世界観測AI

```

を構築する研究プロジェクトである。

目的

```

世界の変化を観測
↓
パターン理解
↓
未来リスク予測
↓
判断支援

```

用途

```

家族の安全
資産防衛
世界理解

```

---

# 2. System Architecture

GenesisPrediction v2 の構造

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
UIはanalysisを読む
UIは再計算しない

```

---

# 3. Observation System

現在のGenesisPrediction v2 は

```

Observation System

```

として動作している。

構造

```

scripts
↓
analysis
↓
UI

```

analysis は

```

現在の世界状態

```

を表す。

---

# 4. Observation Memory Layer

次フェーズ

```

Observation Memory

```

目的

```

観測データを時系列保存

```

構造

```

analysis
↓
history
↓
prediction

```

例

```

sentiment trend
risk evolution
health trend
pattern detection

```

---

# 5. Repository Memory

GenesisPrediction には

```

Repository Memory

```

が存在する。

AIはまず

```

docs/repository_memory_index.md

```

を読む。

これは

```

プロジェクト知識ベース

```

の目次である。

---

# 6. Knowledge Load Order

AIは以下の順で知識をロードする。

Step 1

```

docs/ai_quick_context.md

```

20秒理解

Step 2

```

docs/repository_memory_index.md

```

知識ベース目次

Step 3

```

docs/genesis_system_map.md

```

システム全体構造

Step 4

Core Architecture

```

docs/repo_map.md
docs/pipeline_system.md
docs/ui_system.md
docs/ui_data_dependencies.md
docs/analysis_data_schema.md
docs/prediction_architecture.md

```

---

# 7. Runtime System

GenesisPrediction は

```

Morning Ritual

```

で毎日動作する。

流れ

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

# 8. AI Collaboration Model

GenesisPrediction は

```

Human + AI

```

共同研究である。

Human

```

目的
判断
倫理

```

AI

```

分析
設計補助
コード生成

```

最終決定

```

Human

```

---

# 9. Development Rules

AIは以下のルールを守る。

```

1ターン = 1作業
差分修正禁止
完全ファイル提示

```

重要ルール

```

analysis = Single Source of Truth
UI = read-only

```

---

# 10. AI Startup Procedure

新しいAIは以下を実行する。

Step 1

```

ai_bootstrap.md を読む

```

Step 2

```

ai_quick_context.md

```

Step 3

```

repository_memory_index.md

```

Step 4

```

genesis_system_map.md

```

Step 5

Core Architecture docs

---

# 11. System Evolution

GenesisPrediction は

```

観測AI
↓
時系列AI
↓
予測AI
↓
判断AI

```

へ進化する。

---

# 12. Final Vision

最終目標

```

世界観測AI
↓
未来予測AI
↓
危機回避AI

```

---

END OF DOCUMENT
```
