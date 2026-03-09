# GenesisPrediction Architecture

GenesisPrediction v2 の **全体アーキテクチャ概要**。

このファイルは **システム全体を1枚で理解するための設計図**である。

---

# 1. System Overview

GenesisPrediction は

**Explainable Forecast System**

である。

目的

* 世界の変化を観測する
* 危険信号を早く検出する
* 人間の判断を支援する

未来を断言するシステムではない。

---

# 2. Core Philosophy

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

重要原則

```
Prediction を主役にしない
```

主役は

```
Observation
Trend
Signal
Scenario
```

である。

Prediction は **最終要約**。

---

# 3. System Layers

GenesisPrediction は以下の層で構成される。

```
Data Layer
Pipeline Layer
Analysis Layer
Prediction Layer
UI Layer
```

---

# 4. Repository Architecture

主要ディレクトリ

```
data/
scripts/
analysis/
app/
docs/
```

意味

```
data      = raw data
scripts   = pipeline
analysis  = system truth
app       = UI
docs      = project knowledge
```

---

# 5. Data Flow

システムのデータフロー

```
news APIs
fx APIs
external inputs
```

↓

```
scripts
(fetch / analyze / build)
```

↓

```
analysis/
```

↓

```
prediction layer
```

↓

```
UI dashboards
```

---

# 6. Single Source of Truth

GenesisPrediction の真実は

```
analysis/
```

である。

ルール

```
scripts → analysis を生成
UI → analysis を読む
```

UI は **read-only**。

---

# 7. Morning Ritual

GenesisPrediction は

```
Morning Ritual
```

という日次処理で更新される。

実行

```
scripts/run_morning_ritual.ps1
```

処理内容

```
news fetch
analysis build
sentiment update
digest build
prediction update
UI refresh
```

---

# 8. Prediction Layer

Prediction は以下の構造。

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

Prediction の目的

```
未来を断言する
```

ではない。

目的

```
危険分岐を早く見せる
```

である。

---

# 9. UI Architecture

UI は

```
static dashboards
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

UI は

```
analysis/
```

のデータを読む。

---

# 10. Documentation System

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

# 11. AI Integration

GenesisPrediction は

```
Human + AI
```

共同研究プロジェクト。

AIの役割

* 設計補助
* 実装補助
* 分析補助

AIは

```
最終判断を行う存在
```

ではない。

最終判断は **Human**。

---

# 12. Final Principle

GenesisPrediction の目的

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

# End

---

