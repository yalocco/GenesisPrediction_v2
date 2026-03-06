了解しました 👍
では **そのまま保存できる完全ファイル**を出します。
（あなたのルール：**差分なし・完全ファイル**）

これは **情報源に入れてもOK／入れなくてもOK**ですが、
入れておくと **新しいAI・ローカルLLM・新スレ開始時**に非常に効きます。

保存先：

```
docs/AI_PROJECT_BOOTSTRAP.md
```

---

# docs/AI_PROJECT_BOOTSTRAP.md（完全ファイル）

```md
# AI Project Bootstrap
GenesisPrediction v2

Status: Active  
Purpose: 新しいAIが30秒でプロジェクトを理解するための入口  
Last Updated: 2026-03-06

---

# 0. Purpose

このファイルは

```

新しいAI
新しいチャット
ローカルLLM

```

が GenesisPrediction v2 を **即座に理解するための入口**である。

AIはまずこのファイルを読み、
その後必要なドキュメントへ進む。

---

# 1. Project Summary

GenesisPrediction v2 は

```

世界観測
↓
分析
↓
将来予測
↓
意思決定支援

```

を目的とする  
**AI共同研究プロジェクト**である。

主な用途

- 世界情勢の観測
- リスク兆候の検出
- FX判断補助
- 将来予測研究

---

# 2. Core System Architecture

GenesisPrediction の基本構造

```

data
↓
scripts
↓
analysis
↓
UI

```

意味

```

data      = 素材
scripts   = 生成処理
analysis  = Single Source of Truth
UI        = 表示

```

重要原則

```

UIはanalysisのみ読む
UIは再計算しない

```

---

# 3. Single Source of Truth

GenesisPrediction v2 の

```

唯一の真実

```

は

```

analysis/

```

である。

役割

```

scripts → analysis を生成
analysis → UIが読む

```

---

# 4. Main Components

## Data

```

data/

```

ニュース素材

例

```

data/world_politics/YYYY-MM-DD.json

```

---

## Scripts

```

scripts/

```

主な役割

```

fetch
analyze
aggregate
publish
health

```

例

```

run_daily_with_publish.ps1
run_daily_fx_overlay.ps1
build_data_health.py

```

---

## Analysis

```

analysis/

```

最終成果データ

例

```

daily_news
sentiment
digest
overlay
health

```

---

## UI

```

app/static/

```

ページ

```

index.html
overlay.html
sentiment.html
digest.html

```

UIは **analysisのみ参照**する。

---

# 5. Daily Operation

毎日の基本運用

```

Morning Ritual

```

コマンド

```

powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

```

処理

```

fetch
analysis生成
FX overlay
healthチェック

```

---

# 6. Repository Memory

AIが読むべき知識

```

docs/

```

主なドキュメント

Core Architecture

```

repo_map.md
pipeline_system.md
ui_system.md
ui_data_dependencies.md
analysis_data_schema.md
prediction_architecture.md

```

Operation

```

runbook_morning.md
working_agreement.md
chat_operating_rules.md

```

System State

```

project_status.md
system_history.md
decision_log.md

```

Debug

```

debug_playbook.md

```

Roadmap

```

genesis_prediction_roadmap.md

```

---

# 7. Development Rules

AI作業ルール

```

1ターン = 1作業
差分提案禁止
完全ファイル提示

```

理由

```

コピペ事故防止
AI生成欠落防止

```

---

# 8. Debug Principle

問題が起きた場合

```

UI
↓
analysis
↓
scripts

```

の順で確認する。

GenesisPrediction の真実は

```

analysis/

```

である。

---

# 9. Long Term Vision

GenesisPrediction の最終目標

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

# 10. AI Collaboration

GenesisPrediction は

```

Human + AI

```

の共同研究である。

Human

```

目的
判断
倫理

```

AI

```

観測
分析
予測

```

---

# 11. First Action for AI

AIが最初に読むべきドキュメント

```

docs/repo_map.md
docs/project_status.md
docs/pipeline_system.md

```

これで

```

構造
現在地
処理フロー

```

を理解できる。

---

END OF DOCUMENT
```
