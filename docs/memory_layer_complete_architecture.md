# Memory Layer Complete Architecture
GenesisPrediction v2

Status: Draft  
Purpose: GenesisPrediction v2 の Memory Layer と Prediction System の完成アーキテクチャを定義する  
Last Updated: 2026-03-08

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 における

Memory Layer

の完全アーキテクチャを定義する。

目的

・Observation Memory の役割を明確にする  
・Prediction System との接続構造を固定する  
・将来の Trend / Pattern / Prediction AI の基盤を作る  

---

# 1. System Overview

GenesisPrediction v2 の構造

```

External World
↓
Data Sources
↓
Scripts / Pipelines
↓
analysis (Runtime SST)
↓
Observation Memory
↓
Trend Layer
↓
Pattern Layer
↓
Prediction Layer
↓
Prediction Memory
↓
Prediction Index
↓
UI / Decision Support

```

---

# 2. Runtime Layer

Runtime Layer は

```

analysis/

```

である。

役割

・現在の世界状態  
・現在の分析結果  
・現在の予測結果  

GenesisPrediction の重要原則

```

analysis = Single Source of Truth

```

UI は必ず analysis を参照する。

UI は再計算を行わない。

---

# 3. Observation Memory Layer

Observation Memory は

```

analysis/latest
↓
history/YYYY-MM-DD snapshots

```

の構造で保存される。

目的

・世界観測データの保存  
・時系列分析の基盤  
・トレンド検出の材料  

例

```

sentiment_latest.json
daily_summary_latest.json
health_latest.json
prediction_latest.json

```

これらは日次 snapshot として保存される。

---

# 4. Observation History Structure

基本構造

```

data/world_politics/history/

```

日付ディレクトリ

```

history/
├── 2026-03-07/
│   ├── sentiment.json
│   ├── summary.json
│   ├── health.json
│   └── prediction.json
│
├── 2026-03-08/
│   ├── sentiment.json
│   ├── summary.json
│   ├── health.json
│   └── prediction.json

```

保存タイミング

Morning Ritual 完了後

---

# 5. Trend Layer

Trend Layer は

Observation Memory を分析して

変化の方向

を検出する。

入力

```

history data

```

出力

```

trend_latest.json

```

例

```

sentiment worsening trend
risk increasing trend
confidence drop trend
fx volatility trend

```

役割

```

変化を検出する

```

---

# 6. Pattern Layer

Pattern Layer は

Trend の継続・繰り返し・異常

を検出する。

入力

```

trend data

```

出力

```

pattern_latest.json

```

例

```

watchpoint persists for 5 days
risk rising for 4 days
confidence falling trend

```

役割

```

変化の型を理解する

```

---

# 7. Prediction Layer

Prediction Layer は

Trend と Pattern をもとに

未来の可能性

を生成する。

構造

```

Trend Engine
↓
Signal Engine
↓
Scenario Engine
↓
Prediction Engine

```

出力

```

analysis/prediction/

```

主なファイル

```

trend_latest.json
signal_latest.json
scenario_latest.json
prediction_latest.json

```

---

# 8. Prediction Memory

Prediction も履歴保存される。

構造

```

analysis/prediction/history/YYYY-MM-DD/

```

保存内容

```

trend.json
signal.json
scenario.json
prediction.json

```

目的

```

予測の変化を追跡する
prediction drift を検出する

```

---

# 9. Prediction Index

Prediction History を高速に読むため

index が生成される。

ファイル

```

analysis/prediction/prediction_history_index.json

```

生成

```

scripts/build_prediction_history_index.py

```

目的

・高速UI読み込み  
・履歴window slicing  
・prediction drift 可視化  

---

# 10. UI / Decision Support Layer

現在の UI

```

index.html
overlay.html
sentiment.html
digest.html

```

将来追加予定

```

prediction.html
prediction_history.html

```

役割

```

現在状態の可視化
予測の可視化
予測の変化の可視化
判断支援

```

重要原則

```

UI = read-only

```

UI は analysis / prediction を読むだけである。

---

# 11. Daily Heartbeat

GenesisPrediction は

Morning Ritual

で毎日動作する。

処理フロー

```

git pull
↓
run_morning_ritual.ps1
↓
data fetch
↓
analysis build
↓
sentiment build
↓
digest build
↓
FX lane
↓
observation artifacts
↓
history snapshot
↓
prediction pipeline
↓
prediction history write
↓
prediction index build
↓
GUI update

```

Morning Ritual は

```

観測の心拍
記憶の心拍
予測の心拍

```

である。

---

# 12. Conceptual Flow

GenesisPrediction の知能フロー

```

observe
↓
remember
↓
detect change
↓
recognize pattern
↓
predict
↓
remember prediction
↓
show drift
↓
support decision

```

---

# 13. Final System Vision

GenesisPrediction の最終構造

```

World Observation AI
↓
Observation Memory AI
↓
Trend Detection AI
↓
Pattern Recognition AI
↓
Prediction AI
↓
Prediction Memory AI
↓
Decision Support AI

```

これは最終的に

```

世界観測AI
↓
時系列AI
↓
予測AI
↓
判断AI

```

へ進化する。

---

END OF DOCUMENT
```
