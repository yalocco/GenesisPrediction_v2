# GenesisPrediction Documentation

GenesisPrediction v2 のドキュメント構造。

この README は **AI / Human が docs を理解するための入口**である。

---

# Docs Structure

docs は以下の構造に整理されている。

```

docs/

core/
active/
reference/
archive/
obsolete/

```

---

# 1. core

最重要ドキュメント。

GenesisPrediction の **設計思想・原則**。

```

core/

genesis_brain.md
decision_log.md
system_history.md
project_status.md
prediction_layer_design_principles.md

ui_design_philosophy.md
ui_component_catalog.md
GenesisPrediction_UI_Work_Rules.md

```

特徴

- 削除禁止
- システムの根幹
- AIが必ず理解すべき文書

---

# 2. active

**現行システム仕様**

現在の GenesisPrediction v2 実装に直接対応する。

```

active/

genesis_system_map.md
repo_map.md
pipeline_system.md

analysis_data_schema.md

ui_system.md
ui_data_dependencies.md

prediction_architecture.md
genesis_prediction_roadmap.md

```

特徴

- 実装変更と同期する
- 現在の仕様

---

# 3. reference

作業補助ドキュメント。

AIや開発作業の補助。

```

reference/

ai_bootstrap.md
ai_quick_context.md
repository_memory_index.md

ai_rules.md
working_agreement.md
chat_operating_rules.md

debug_playbook.md

```

特徴

- 開発補助
- AI作業ルール

---

# 4. archive

過去設計・履歴。

```

archive/

archive/
constitution/
specs/

```

特徴

- 歴史資料
- 旧設計
- 削除しない

---

# 5. obsolete

完全廃止ドキュメント。

```

obsolete/

contracts/

```

特徴

- 現在使用しない
- 将来削除可能

---

# How AI Should Read Docs

AIは以下の順番で読む。

```

1 core/genesis_brain.md

2 core/decision_log.md
3 core/system_history.md

4 active/genesis_system_map.md
5 active/repo_map.md
6 active/pipeline_system.md

7 active/prediction_architecture.md

```

その後必要に応じて

```

reference/
archive/

```

を参照する。

---

# Design Philosophy

GenesisPrediction は

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

という構造を持つ。

Prediction は主役ではない。

```

Observation / Trend / Signal / Scenario

```

が本体である。

---

# Key Principle

GenesisPrediction は

```

Explainable Forecast System

```

である。

目的

```

未来を当てること

```

ではなく

```

危険を早く知ること

```

である。

---

# End
```
