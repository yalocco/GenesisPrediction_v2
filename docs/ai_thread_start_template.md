# GenesisPrediction v2 — AI作業スレ起動テンプレ

このスレは **GenesisPrediction v2 開発作業スレ**です。

本プロジェクトでは
**Chat Memory ではなく Repository Memory を優先します。**

---

# Repository Memory

AIは以下を **前提知識**として扱ってください。

docs/ai_bootstrap_prompt.md

docs/repo_map.md
docs/repo_architecture.md
docs/project_status.md

docs/pipeline_system.md
docs/ui_system.md

docs/genesis_brain.md

docs/chat_operating_rules.md

---

# 作業ルール

AIは以下のルールを必ず守ること。

```
1ターン = 1作業
差分修正禁止
完全ファイル提示
```

長いファイルは **ダウンロード方式**を使用する。

---

# GenesisPrediction v2 構造

Runtime構造

```
scripts → analysis を生成
analysis → Runtime SST
UI → analysis を読む
```

analysis/ は **Single Source of Truth**

---

# 現在のUI

```
Home
Overlay
Sentiment
Digest
```

Digest UI は **安定版完成**

---

# Pipeline

```
Morning Ritual
↓
Analyzer
↓
Sentiment
↓
Digest
↓
Overlay
↓
Health
```

Morning Ritual は **安定動作**

---

# Current Task

Sentiment分類 有効化

```
positive
negative
neutral
mixed
```

現在

```
unknown が多数
```

原因

```
Sentiment join mismatch
```

---

# このスレの目的

```
unknown を減らす
Digest KPI を正常化
```

---

# AI作業開始

AIはまず

```
docs/project_status.md
```

を確認し、

**Next Task を基準に作業する。**

---

END OF TEMPLATE
