# GenesisPrediction AI Start Guide

このファイルは **GenesisPrediction を扱う AI の最初の入口**である。

新しい AI / 新しいスレ / 新しい LLM は  
まずこのファイルを読む。

---

# 1. Project Overview

GenesisPrediction は

```

Explainable Forecast System

```

である。

目的

```

未来を当てること

```

ではない。

目的は

```

危険を早く知ること

```

である。

---

# 2. System Philosophy

GenesisPrediction の基本構造

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

重要原則

```

Prediction は主役ではない

```

主役は

```

Observation
Trend
Signal
Scenario

```

である。

---

# 3. Repository Structure

重要ディレクトリ

```

data/
scripts/
analysis/
app/
docs/

```

意味

```

data     = raw data
scripts  = pipeline
analysis = single source of truth
app      = UI
docs     = knowledge

```

---

# 4. Single Source of Truth

GenesisPrediction の真実は

```

analysis/

```

である。

```

scripts → analysis を生成
UI → analysis を読む

```

UIは **read-only**。

---

# 5. Documentation Structure

docs は以下の構造。

```

docs/

core/
active/
reference/
archive/
obsolete/

```

意味

```

core      = 設計思想
active    = 現行仕様
reference = 作業補助
archive   = 過去設計
obsolete  = 廃止

```

---

# 6. How AI Should Read Docs

AIは以下の順序で読む。

Step 1

```

docs/core/genesis_brain.md

```

Step 2

```

docs/core/decision_log.md
docs/core/system_history.md

```

Step 3

```

docs/active/genesis_system_map.md
docs/active/repo_map.md
docs/active/pipeline_system.md

```

Step 4

```

docs/active/prediction_architecture.md

```

必要に応じて

```

docs/reference/
docs/archive/

```

---

# 7. Key Operational Rules

GenesisPrediction AI作業ルール

```

1ターン = 1作業
差分提案禁止
完全ファイルのみ
削除前に分類

```

UI作業ルール

```

長文貼り付け禁止
download生成優先
zip fallback

```

---

# 8. Morning Ritual

GenesisPrediction は

```

Morning Ritual

```

という日次処理で更新される。

実行

```

scripts/run_morning_ritual.ps1

```

処理

```

news fetch
analysis build
digest build
prediction build
UI update

```

---

# 9. AI Role

AIの役割

```

設計補助
実装補助
分析補助

```

AIは

```

予測を断言する存在

```

ではない。

AIは

```

Humanの判断支援

```

のために存在する。

---

# 10. Final Principle

GenesisPrediction は

```

Human + AI

```

共同研究プロジェクトである。

目的

```

世界の変化を理解する
危険信号を早く見つける
判断を助ける

```

---

# End
```
