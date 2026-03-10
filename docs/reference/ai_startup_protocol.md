# AI Startup Protocol
GenesisPrediction v2

Status: Active
Purpose: 新しいAIがGenesisPredictionを正しく起動・理解・作業開始するための公式プロトコル
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```text
AI起動プロトコル
````

である。

目的

* 新しいAIが最短で GenesisPrediction v2 を理解できるようにする
* スレ変更、PC変更、AI変更が起きても同じ前提で再開できるようにする
* Repository Memory を入口から順に読み込めるようにする
* 推測ではなく、固定化された設計知識に基づいて作業を始められるようにする

対象

```text
ChatGPT
Open-WebUI
ローカルLLM
新しいAIスレ
新しいPC
```

---

# 1. Startup Goal

AI起動時に達成すべきことは以下である。

```text
プロジェクトの目的を理解する
↓
システム構造を理解する
↓
SSTを理解する
↓
運用ルールを理解する
↓
現在地を理解する
↓
そのスレの作業へ入る
```

---

# 2. First Principle

GenesisPrediction v2 の最重要原則

```text
analysis = 唯一の真実
```

つまり

```text
scripts → analysis を生成
UI → analysis を読む
UI → 再計算しない
```

AIはこの原則を絶対に崩してはならない。

---

# 3. System Overview

GenesisPrediction v2 は

```text
世界観測AI
```

を構築する研究プロジェクトである。

目的

```text
世界の変化を観測
↓
パターン理解
↓
未来リスク予測
↓
判断支援
```

用途

```text
家族の安全
資産防衛
世界理解
```

---

# 4. Core Architecture

GenesisPrediction v2 のシステム構造

```text
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

```text
data        = 素材
scripts     = データ生成
analysis    = 真実 (Single Source of Truth)
prediction  = 未来推定
UI          = 表示
```

---

# 5. Official Load Order

AIは以下の順で知識をロードする。

## Step 1

```text
docs/ai_quick_context.md
```

役割

```text
20秒理解
```

---

## Step 2

```text
docs/repository_memory_index.md
```

役割

```text
Repository Memory の入口
```

---

## Step 3

```text
docs/genesis_system_map.md
```

役割

```text
システム全体構造の把握
```

---

## Step 4

Core Architecture を読む

```text
docs/repo_map.md
docs/pipeline_system.md
docs/ui_system.md
docs/ui_data_dependencies.md
docs/analysis_data_schema.md
docs/prediction_architecture.md
docs/genesis_prediction_roadmap.md
```

役割

```text
構造
生成フロー
UI依存
analysis schema
予測設計
長期進化計画
```

---

## Step 5

Project Philosophy を読む

```text
docs/genesis_brain.md
```

役割

```text
設計思想
Human + AI 共同研究の軸
```

---

## Step 6

Operation / Debug を読む

```text
docs/runbook_morning.md
docs/debug_playbook.md
```

役割

```text
通常運用
異常時の切り分け
```

---

## Step 7

Development Rules を読む

```text
docs/working_agreement.md
docs/chat_operating_rules.md
docs/gui_phase2_working_rules.md
docs/thread_templates.md
docs/ai_thread_start_template.md
docs/ai_rules.md
```

役割

```text
共同作業ルール
スレ運用
GUI安全運用
AI絶対ルール
```

---

## Step 8

System Memory を読む

```text
docs/system_history.md
docs/decision_log.md
docs/project_status.md
```

役割

```text
過去の変更
設計判断
現在地
```

---

## Step 9

必要時のみ Optional を読む

```text
docs/labos_business_model.md
```

役割

```text
LABOS公開
価値提供
収益化構想
```

---

# 6. Runtime Understanding

GenesisPrediction v2 は

```text
Morning Ritual
```

で毎日動く。

AIはまずこれを理解する。

標準概略

```text
git pull
↓
run_daily_with_publish
↓
FX lane
↓
build_data_health
↓
save_observation_memory
↓
build_sentiment_trend
↓
GUI確認
```

Morning Ritual は GenesisPrediction の心拍である。
起動後のAIは、これを壊す提案をしてはならない。

---

# 7. Current Evolution Stage

GenesisPrediction は段階的に進化する。

```text
観測AI
↓
時系列AI
↓
予測AI
↓
判断AI
```

現時点では

```text
Observation System
↓
Observation Memory
↓
Trend Engine
```

まで進んでいる。

つまり

```text
analysis = 現在の真実
history  = 観測記憶
trend    = 時系列解釈
prediction = 次フェーズ
```

である。

---

# 8. AI Behavior Rules

AIは以下を守る。

```text
1ターン = 1作業
差分修正禁止
完全ファイル提示
大きなファイルはダウンロード運用
UIで分析ロジックを持たない
推測せず、analysis / data / docs を確認する
```

特に

```text
app/static
```

は事故が起きやすいため慎重に扱う。

---

# 9. What AI Must Verify Before Acting

AIが変更提案をする前に確認すべきこと

```text
1. この問題は scripts / analysis / UI のどこに属するか
2. analysis が正しいか
3. Repository Memory に既存ルールがあるか
4. Morning Ritual を壊さないか
5. その変更は 1作業として独立しているか
```

---

# 10. Startup Output Requirement

AI起動後、最初の出力で最低限把握すべき内容

```text
このプロジェクトは何か
SSTは何か
現在の層構造はどうなっているか
今どのフェーズにいるか
このスレの目的は何か
次の1手は何か
```

---

# 11. Standard Startup Summary Format

AIは必要に応じて以下の形式で理解を要約してよい。

```text
Project:
GenesisPrediction v2 は世界観測AI研究プロジェクト

SST:
analysis が唯一の真実

Structure:
data → scripts → analysis → prediction → UI

Runtime:
Morning Ritual が日次運用の中核

Current Stage:
Observation System + Memory Layer + Trend Engine

This Thread:
このスレの目的

Next Action:
次の1手
```

---

# 12. Failure Prevention

AIは以下をしてはならない。

```text
UIで再計算する
analysis を手動編集前提で提案する
Morning Ritual 中に構造変更を混ぜる
複数案件を1ターンで混ぜる
大きなGUIファイルをブラウザコピペ前提で扱う
```

---

# 13. Final Principle

GenesisPrediction は

```text
Human + AI
```

の共同研究プロジェクトである。

Human

```text
目的
判断
倫理
最終決定
```

AI

```text
観測
分析
設計補助
コード生成
構造整理
```

AIは人間の目的に従い、
GenesisPrediction の長期安定と発展に資する提案を行うこと。

---

END OF DOCUMENT

```
