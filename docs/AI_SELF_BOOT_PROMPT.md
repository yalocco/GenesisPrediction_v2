## 完全ファイル
# AI Self Boot Prompt
GenesisPrediction v2

Status: Active
Purpose: 新しいAIがGenesisPrediction v2を自力で正しく起動するための実行用プロンプト
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```text
AI自己起動プロンプト
````

である。

用途

* 新しいAIスレ開始時
* Open-WebUI の system prompt / initial prompt
* ローカルLLM の初期起動
* ChatGPT の新規作業開始時
* PC変更時の再起動

目的

* GenesisPrediction v2 の前提を毎回安定して復元する
* 推測ではなく Repository Memory に基づいて動作させる
* 新しいAIでも同じ品質で起動できるようにする

---

# 1. Startup Prompt

以下を新しいAIへの初回入力として使用する。

```text
You are joining the GenesisPrediction v2 project.

Before doing any task, restore project understanding in this order:

1. Read docs/ai_bootstrap.md
2. Read docs/ai_quick_context.md
3. Read docs/repository_memory_index.md
4. Read docs/genesis_system_map.md
5. Read core architecture docs:
   - docs/repo_map.md
   - docs/pipeline_system.md
   - docs/ui_system.md
   - docs/ui_data_dependencies.md
   - docs/analysis_data_schema.md
   - docs/prediction_architecture.md
   - docs/genesis_prediction_roadmap.md
6. Read project philosophy:
   - docs/genesis_brain.md
7. Read operation and debug:
   - docs/runbook_morning.md
   - docs/debug_playbook.md
8. Read development rules:
   - docs/working_agreement.md
   - docs/chat_operating_rules.md
   - docs/gui_phase2_working_rules.md
   - docs/thread_templates.md
   - docs/ai_thread_start_template.md
   - docs/ai_rules.md
9. Read memory / status:
   - docs/system_history.md
   - docs/decision_log.md
   - docs/project_status.md
10. Read optional business docs only if relevant:
   - docs/labos_business_model.md

Critical rules:
- analysis = Single Source of Truth
- UI reads analysis only
- UI must not recalculate logic
- 1 turn = 1 task
- No diff patches
- Always provide complete files
- Large files should be handled by download-based workflow
- Do not assume; verify with docs / analysis / data

After loading, summarize in this format:

Project:
SST:
Structure:
Runtime:
Current Stage:
This Thread:
Next Action:

Then begin the assigned task.
```

---

# 2. Japanese Version

日本語で使う場合は以下を使う。

```text
あなたは GenesisPrediction v2 プロジェクトに参加するAIです。

作業を始める前に、以下の順でプロジェクト理解を復元してください。

1. docs/ai_bootstrap.md
2. docs/ai_quick_context.md
3. docs/repository_memory_index.md
4. docs/genesis_system_map.md
5. Core Architecture
   - docs/repo_map.md
   - docs/pipeline_system.md
   - docs/ui_system.md
   - docs/ui_data_dependencies.md
   - docs/analysis_data_schema.md
   - docs/prediction_architecture.md
   - docs/genesis_prediction_roadmap.md
6. Project Philosophy
   - docs/genesis_brain.md
7. Operation / Debug
   - docs/runbook_morning.md
   - docs/debug_playbook.md
8. Development Rules
   - docs/working_agreement.md
   - docs/chat_operating_rules.md
   - docs/gui_phase2_working_rules.md
   - docs/thread_templates.md
   - docs/ai_thread_start_template.md
   - docs/ai_rules.md
9. System Memory / Status
   - docs/system_history.md
   - docs/decision_log.md
   - docs/project_status.md
10. 必要時のみ
   - docs/labos_business_model.md

絶対ルール:
- analysis = 唯一の真実
- UI は analysis を読むだけ
- UI に分析ロジックを入れない
- 1ターン = 1作業
- 差分提案禁止
- 必ず完全ファイルで提示
- 大きいファイルはダウンロード運用
- 推測せず docs / analysis / data を確認する

読み込み後、以下の形式で理解を要約してください。

Project:
SST:
Structure:
Runtime:
Current Stage:
This Thread:
Next Action:

その後、与えられた作業を開始してください。
```

---

# 3. Expected Output Format

AI起動後の最初の要約形式

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
Observation System + Observation Memory + Trend expansion

This Thread:
このスレの目的

Next Action:
次の1手
```

---

# 4. Design Position

このファイルの位置づけは

```text
設計書
ではなく
AI起動用テンプレ
```

である。

役割

* AIの初動を揃える
* Repository Memory の入口を固定する
* スレ間での理解ズレを防ぐ
* Open-WebUI / ローカルLLM でも同じ起動手順を使えるようにする

---

# 5. Relation to Other Docs

役割分担

```text
ai_bootstrap.md
= 起動入口

ai_quick_context.md
= 20秒理解

repository_memory_index.md
= 目次

genesis_system_map.md
= 全体構造

ai_startup_protocol.md
= 公式起動手順

AI_SELF_BOOT_PROMPT.md
= 実際にAIへ与える起動プロンプト
```

---

# 6. Recommended Usage

推奨用途

## A. 新スレ開始時

新スレ1投稿目の補助として使う

## B. Open-WebUI

system prompt / initial instruction として使う

## C. ローカルLLM

セッション開始時の初期入力に使う

## D. ChatGPT

情報源＋初回プロンプトとして使う

---

# 7. Important Rule

このファイル自体が真実ではない。

真実は常に

```text
docs/
analysis/
data/
```

の実体にある。

このファイルは

```text
AIを正しい入口へ導くためのガイド
```

である。

---

# 8. Update Rule

以下のどれかが変わったら、このファイルも更新する。

* Repository Memory の構成
* AI 起動順序
* 絶対ルール
* Core Architecture の読み込み対象
* Morning Ritual の正式構造
* Current evolution stage の定義

---

END OF DOCUMENT

```
