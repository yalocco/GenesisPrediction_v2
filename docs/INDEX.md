# Docs Index (GenesisPrediction v2)

このファイルは **docs ディレクトリのナビゲーション（目次）** です。

GenesisPrediction v2 のドキュメントは

```
Human Operation
AI Design
Project Architecture
```

の **3つの役割**で整理されています。

---

# 🤖 AI Bootstrap

新しい AI を起動する場合は **最初に読む**

```
ai_bootstrap_prompt.md
```

AIの初期化と Repository Memory の読み込みを行う。

---

# 🧠 Repository Architecture

プロジェクトの設計構造。

| File                 | Purpose                           |
| -------------------- | --------------------------------- |
| repo_architecture.md | Chat / Repository / Project の三層構造 |
| repo_map.md          | リポジトリ構造の地図                        |
| project_status.md    | 現在の状態 / 作業中テーマ                    |

---

# ⚙ Pipeline System

GenesisPrediction のデータ生成構造。

| File               | Purpose   |
| ------------------ | --------- |
| pipeline_system.md | パイプライン構造  |
| runbook_morning.md | 毎日の正式運用手順 |

---

# 🖥 UI System

GUIの設計。

| File                        | Purpose                |
| --------------------------- | ---------------------- |
| ui_system.md                | UI構造 / HTML依存 / JSON依存 |
| gui_phase2_working_rules.md | GUI運用ルール               |

---

# 🤖 AI Collaboration Rules

AIと人間の共同開発ルール。

| File                    | Purpose |
| ----------------------- | ------- |
| chat_operating_rules.md | AI作業ルール |
| working_agreement.md    | 共同開発ルール |

---

# 🧩 Design Philosophy

GenesisPrediction の思想。

| File             | Purpose                 |
| ---------------- | ----------------------- |
| genesis_brain.md | 設計思想 / SST / Pipeline哲学 |

---

# 🧭 Human Operation Docs

人間運用用ドキュメント。

| File              | Purpose |
| ----------------- | ------- |
| observation.md    | 観測ログ    |
| assumptions.md    | 分析前提    |
| diff_schema.md    | データ構造説明 |
| fragile_points.md | 壊れやすい箇所 |

---

# 🧠 Knowledge Architecture

GenesisPrediction v2 は以下の **三層構造**で知識を管理する。

```
Chat Memory
↓
Repository Memory (docs)
↓
Project Knowledge
```

---

# 📌 最重要ルール

GenesisPrediction v2 の **Single Source of Truth**

```
analysis/
```

構造

```
scripts → analysis を生成
analysis → 唯一の真実
UI → analysis を表示
```

---

# 🧩 この docs の役割

この docs は

```
AI変更
PC変更
スレ変更
```

が起きても

* プロジェクト構造を即復元
* 作業ルールを保持
* 開発継続可能

にするための **Repository Memory** です。

---

GenesisPrediction v2 は
**AIと人間の共同開発プロジェクト**である。
