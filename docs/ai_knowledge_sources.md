# AI Knowledge Sources (GenesisPrediction v2)

このファイルは
**AIが読むべき Repository Memory（情報源）を固定するリスト**です。

新しい AI を設定する場合は
以下のドキュメントを **Knowledge Source として登録する。**

---

# 🤖 AI Bootstrap

最初に読むファイル

| File                   | Purpose   |
| ---------------------- | --------- |
| ai_bootstrap_prompt.md | AI起動プロンプト |

---

# 🧠 Repository Architecture

プロジェクト構造を理解するためのドキュメント

| File                 | Purpose                          |
| -------------------- | -------------------------------- |
| repo_architecture.md | Chat / Repository / Project 三層構造 |
| repo_map.md          | リポジトリ構造の地図                       |
| project_status.md    | 現在の状態                            |

---

# ⚙ System Design

システム構造

| File               | Purpose  |
| ------------------ | -------- |
| pipeline_system.md | パイプライン構造 |
| ui_system.md       | UI構造     |

---

# 🧩 Design Philosophy

プロジェクト思想

| File             | Purpose                 |
| ---------------- | ----------------------- |
| genesis_brain.md | 設計思想 / SST / Pipeline哲学 |

---

# 🤖 AI Collaboration Rules

AIと人間の共同作業ルール

| File                    | Purpose |
| ----------------------- | ------- |
| chat_operating_rules.md | AI作業ルール |

---

# 📌 Knowledge Source Summary

AI Knowledge Source に登録するファイル

```
docs/ai_bootstrap_prompt.md

docs/repo_architecture.md
docs/repo_map.md
docs/project_status.md

docs/pipeline_system.md
docs/ui_system.md

docs/genesis_brain.md

docs/chat_operating_rules.md
```

---

# 🚫 Knowledge Source に入れないもの

以下は **AI knowledge source には不要**

```
README.md
INDEX.md

runbook_morning.md
working_agreement.md
gui_phase2_working_rules.md
```

理由

* 人間運用ドキュメント
* ナビゲーション
* AI設計知識ではない

---

# 🧠 Knowledge Architecture

GenesisPrediction v2 は以下の **三層構造**で知識を管理する

```
Chat Memory
↓
Repository Memory
↓
Project Knowledge
```

Repository Memory が

```
docs/
```

である。

---

# 🎯 目的

この構造により

* 新しいAI
* 新しいスレ
* 新しいPC

でも

**プロジェクト構造を即復元できる。**

---

GenesisPrediction v2 は
**AIと人間の共同開発プロジェクト**である。
