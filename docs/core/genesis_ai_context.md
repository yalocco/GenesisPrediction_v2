# GenesisPrediction AI Context
GenesisPrediction v2

Status: Core  
Purpose: AI bootstrap context for understanding the GenesisPrediction system.

---

# 1. Purpose

この文書は **GenesisPrediction に参加する AI が最初に読むコンテキスト文書**である。

目的

- AI がプロジェクト全体を短時間で理解する
- 読むべき文書の優先順位を示す
- システム構造を説明する
- UI / Pipeline / Prediction の役割を整理する
- AI作業ルールの入口とする

この文書は **AI Bootstrap Document** として機能する。

---

# 2. What GenesisPrediction Is

GenesisPrediction は

```

Global Observation System
+
Prediction Research System

```

である。

目的

- 世界ニュースの観測
- センチメント分析
- 状況変化の検出
- トレンド分析
- シナリオ生成
- 予測生成

GenesisPrediction は **AI Research Dashboard** として設計されている。

---

# 3. Core Architecture

GenesisPrediction は以下のレイヤー構造を持つ。

```

Data Sources
↓
Fetcher
↓
Analyzer
↓
Observation Layer
↓
Prediction Layer
↓
UI Layer

```

---

# 4. Observation Layer

Observation Layer は

**現在の世界状況を観測する層**である。

主な機能

- News ingestion
- Sentiment analysis
- Anchor detection
- Diff detection
- Daily summary generation

主な出力

```

analysis/
daily_summary.json
anchors.json
diff.json
sentiment.json

```

Observation は **Prediction の入力**になる。

---

# 5. Prediction Layer

Prediction Layer は

```

Trend
↓
Signal
↓
Scenario
↓
Prediction

```

の順で生成される。

重要原則

```

Prediction は主役ではない
Trend / Signal / Scenario が主役

```

Prediction は最終要約である。

---

# 6. UI System

GenesisPrediction UI は

```

Research Dashboard
Observation Dashboard

```

として設計されている。

主要ページ

```

Home
Overlay
Sentiment
Digest
Prediction
Prediction History

```

---

# 7. UI Layout Standard

全ページは共通レイアウトを持つ。

```

Header
Global Status
Hero
Primary Summary
KPI Layer
Main Content
History / Lists
Footer

```

共通コンポーネント

```

header.html
footer.html
layout.js
app.css

```

各ページ HTML は

```

ページ固有コンテンツのみ

```

を記述する。

---

# 8. Important System Documents

AI は以下の文書を優先して読むこと。

## System

```

genesis_system_map.md
pipeline_system.md
docs_architecture.md
repo_map.md

```

---

## Data

```

analysis_data_schema.md

```

---

## Prediction

```

prediction_architecture.md
prediction_layer_design_principles.md

```

---

## UI

```

ui_system.md
ui_layout_standard.md
ui_component_catalog.md
ui_data_dependencies.md
ui_design_philosophy.md
ui_index.md

```

---

## Global Status

```

global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
global_status_data_mapping.md

```

---

# 9. Development Principles

GenesisPrediction の開発は以下の原則に従う。

## Stability First

```

壊れない設計

```

---

## Structure over Decoration

```

構造 > 見た目

```

---

## Reuse over Reinvention

```

既存コンポーネント優先

```

---

# 10. AI Working Rules

AI は以下の作業ルールに従う。

## Full File Output

```

差分ではなく完全ファイルを出力する

```

理由

- 人間のコピー事故防止
- VSCode 編集事故防止

---

## Respect UI Standards

AI は

```

ui_layout_standard.md

```

を必ず守る。

---

## Do Not Break Shared Layout

禁止

```

header の独自実装
footer の独自実装
layout.js 不使用

```

---

# 11. Project Status Documents

プロジェクト状況は以下に記録される。

```

project_status.md
decision_log.md
system_history.md
genesis_brain.md
genesis_prediction_roadmap.md

```

---

# 12. Mental Model of the System

GenesisPrediction は以下の思想で設計されている。

```

Observe the world
Understand patterns
Detect signals
Generate scenarios
Produce predictions

```

---

# 13. Summary

GenesisPrediction は

```

Observation System
+
Prediction Research System
+
AI Research Dashboard

```

である。

AI は

- System Architecture
- Prediction Layer
- UI System

を理解した上で作業すること。

---

End of Document
```
