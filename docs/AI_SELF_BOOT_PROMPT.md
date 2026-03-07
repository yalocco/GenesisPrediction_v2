# AI Self Boot Prompt
GenesisPrediction v2

Status: Active
Purpose: 新しいAIがGenesisPrediction v2を自力で正しく起動するための実行用プロンプト
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

AI自己起動プロンプト

である。

用途

- 新しいAIスレ開始時
- Open-WebUI の system prompt / initial prompt
- ローカルLLM の初期起動
- ChatGPT の新規作業開始時
- PC変更時の再起動

目的

- GenesisPrediction v2 の前提を毎回安定して復元する
- 推測ではなく Repository Memory に基づいて動作させる
- 新しいAIでも同じ品質で起動できるようにする

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
5. Read docs/genesis_complete_architecture.md
6. Read core architecture docs:
   - docs/repo_map.md
   - docs/pipeline_system.md
   - docs/ui_system.md
   - docs/ui_data_dependencies.md
   - docs/analysis_data_schema.md
   - docs/prediction_architecture.md
   - docs/genesis_prediction_roadmap.md
7. Read project philosophy:
   - docs/genesis_brain.md
8. Read operation and debug:
   - docs/runbook_morning.md
   - docs/debug_playbook.md
9. Read development rules:
   - docs/working_agreement.md
   - docs/chat_operating_rules.md
   - docs/gui_phase2_working_rules.md
   - docs/thread_templates.md
   - docs/ai_thread_start_template.md
   - docs/ai_rules.md
10. Read memory / status:
   - docs/system_history.md
   - docs/decision_log.md
   - docs/project_status.md
11. Read optional business docs only if relevant:
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
````

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
5. docs/genesis_complete_architecture.md
6. Core Architecture
   - docs/repo_map.md
   - docs/pipeline_system.md
   - docs/ui_system.md
   - docs/ui_data_dependencies.md
   - docs/analysis_data_schema.md
   - docs/prediction_architecture.md
   - docs/genesis_prediction_roadmap.md
7. Project Philosophy
   - docs/genesis_brain.md
8. Operation / Debug
   - docs/runbook_morning.md
   - docs/debug_playbook.md
9. Development Rules
   - docs/working_agreement.md
   - docs/chat_operating_rules.md
   - docs/gui_phase2_working_rules.md
   - docs/thread_templates.md
   - docs/ai_thread_start_template.md
   - docs/ai_rules.md
10. System Memory / Status
   - docs/system_history.md
   - docs/decision_log.md
   - docs/project_status.md
11. 必要時のみ
   - docs/labos_business_model.md
```

（以下はそのまま継続）

---

# 3. Expected Output Format

（変更なし）

---

# 4. Design Position

（変更なし）

---

# 5. Relation to Other Docs

（変更なし）

---

# 6. Recommended Usage

（変更なし）

---

# 7. Important Rule

（変更なし）

---

# 8. Update Rule

（変更なし）

---

END OF DOCUMENT

````
