# Trend Layer Design
GenesisPrediction v2

Status: Draft
Purpose: Observation から Trend を抽出する設計を定義する
Last Updated: 2026-03-09

---

# 0. Purpose

この文書は

GenesisPrediction における

Trend Layer

を定義する。

目的

- Observation データから変化パターンを検出する
- Signal / Scenario / Prediction の入力を生成する
- 時系列の意味を抽出する

GenesisPrediction の基本構造

Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction

---

# 1. Observation Layer (既存)

Observation は

世界の状態を記録する層。

主なデータ

analysis/

daily_summary_latest.json
sentiment_latest.json
anchors_latest.json
health_latest.json

特徴

- 状態の記録
- 変化の意味はまだ持たない

Observation は

世界の「温度計」

である。

---

# 2. Trend Layer

Trend は

Observation の

変化パターン

を抽出する層である。

役割

- 時系列変化の検出
- ノイズ除去
- パターン識別

Trend は

世界の「流れ」

を表す。

---

# 3. Trend Types

GenesisPrediction では
以下の種類の Trend を扱う。

## 3.1 Sentiment Trend

ニュース感情の変化。

例

sentiment worsening
sentiment recovery
sentiment stability

入力

sentiment_latest.json
sentiment_history

---

## 3.2 Topic Trend

特定トピックの増減。

例

war topic rising
energy topic surge
election topic spike

入力

anchors
article topics

---

## 3.3 Event Density Trend

イベント密度の変化。

例

incident spike
conflict cluster

入力

daily_summary
article classification

---

## 3.4 FX Trend

為替トレンド。

例

JPY weakening
THB volatility
USD shock

入力

fx_overlay data
fx history

---

## 3.5 Risk Trend

複合リスク。

例

energy shock risk
war escalation risk
financial stress

入力

topic + sentiment + FX

---

# 4. Trend Detection Principles

Trend は次の原則で検出する。

## 4.1 Noise Filtering

短期ノイズを除去する。

例

1日だけの spike は trend としない。

---

## 4.2 Direction

Trend は方向を持つ。

values

rising
falling
stable
volatile

---

## 4.3 Strength

Trend の強さ。

range

0.0 – 1.0

---

## 4.4 Confidence

Trend 検出の信頼度。

range

0.0 – 1.0

---

# 5. Trend Output

Trend Layer は

次の JSON を生成する。

analysis/trend_latest.json

---

# 6. Trend JSON Schema

例

```json
{
  "date": "2026-03-09",

  "trends": [

    {
      "id": "sentiment_global",
      "type": "sentiment",
      "direction": "falling",
      "strength": 0.62,
      "confidence": 0.58
    },

    {
      "id": "energy_risk",
      "type": "topic",
      "direction": "rising",
      "strength": 0.71,
      "confidence": 0.63
    },

    {
      "id": "jpy_trend",
      "type": "fx",
      "direction": "weakening",
      "strength": 0.55,
      "confidence": 0.60
    }

  ]

}
````

---

# 7. Relation to Signal Layer

Signal は

Trend の意味を解釈する。

例

Trend

energy risk rising

↓

Signal

energy shock warning

---

# 8. Relation to Scenario Layer

Scenario は

複数 Trend を組み合わせる。

例

energy risk rising
+
war topic rising

↓

Scenario

middle east escalation

---

# 9. Relation to Prediction Layer

Prediction は

Signal と Scenario を統合する。

例

Signal

energy shock warning

↓

Prediction

oil price spike risk

---

# 10. Implementation Plan

実装は段階的に行う。

Phase 1

sentiment trend

Phase 2

topic trend

Phase 3

risk trend

Phase 4

FX trend integration

---

# 11. Location in Pipeline

Pipeline

scripts
↓
analysis (Observation)
↓
Trend Layer
↓
Signal Layer
↓
Scenario Layer
↓
Prediction Layer

---

# 12. Long-term Vision

Trend Layer は

GenesisPrediction の

Pattern Recognition Engine

となる。

目的

世界の変化を

できるだけ早く検知する。

---

END OF DOCUMENT

````
