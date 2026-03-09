# Signal Layer Design
GenesisPrediction v2

Status: Draft
Purpose: Trend から Signal を抽出する設計を定義する
Last Updated: 2026-03-09

---

# 0. Purpose

この文書は

GenesisPrediction における

Signal Layer

を定義する。

目的

- Trend データから重要な兆候を抽出する
- Scenario / Prediction の入力を生成する
- 「変化」から「警告」へ意味を進める
- 未来分岐の手前で Early Warning を固定する

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

Signal Layer は

Trend の意味を解釈し
注意すべき変化だけを取り出す層

である。

---

# 1. Position in GenesisPrediction

Signal Layer は

Prediction Architecture において

Trend Engine
↓
Signal Engine
↓
Scenario Engine

の中央に位置する。  
Trend は「流れ」、Signal は「注意すべき変化」、Scenario は「未来分岐」である。 :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}

Signal の役割

- 流れの中から警告を検出する
- Scenario に渡すべき兆候を整理する
- ノイズではなく **運用に意味のある変化** だけを残す

---

# 2. Trend and Signal Difference

Trend は

世界の流れ

を示す。

例

- sentiment falling
- energy topic rising
- fx volatility rising

Signal は

その流れの中で
**特に注意すべき変化**

を示す。

例

- persistent negative sentiment
- energy shock warning
- currency instability warning
- regime shift warning

重要原則

Trend = flow  
Signal = warning

Trend をそのまま Scenario に渡さない。  
必ず一段 **Signal 化**する。

---

# 3. Core Principle

Signal Layer の最重要原則はこれである。

```text
Signal は “警告として使える変化” だけを出す
````

つまり

* ただの上下動は signal にしない
* 1日だけのノイズは signal にしない
* 人間が見て意味のある warning に絞る

Signal は

```text
Early Warning
```

として機能する。 

---

# 4. Input

Signal Layer の主入力は

```text
analysis/prediction/trend_latest.json
```

である。 

補助的に利用してよいもの

* trend history
* observation memory
* health status

ただし主役は

```text
trend_latest.json
```

であり、

Signal Layer は Observation を直接読んで推論を飛ばさない。

重要原則

```text
Signal は Trend の上に立つ
```

---

# 5. Output

Signal Layer は次を生成する。

```text
analysis/prediction/signal_latest.json
```

Prediction Architecture でも Signal Engine の出力は `signal_latest.json` と定義されている。 

Signal は

* UI に直接見せてもよい
* Scenario Engine へ渡してもよい
* Prediction Engine の drivers の材料にもなる

---

# 6. Signal Types

GenesisPrediction ではまず以下の signal type を扱う。

## 6.1 persistence

同じ Trend が持続している。

例

* negative sentiment persists
* war topic persists
* fx stress persists

意味

短期ノイズではなく
継続的な変化である可能性が高い。

---

## 6.2 acceleration

Trend の速度が上がる。

例

* risk rising faster
* volatility increasing faster
* topic surge accelerating

意味

警戒度を上げるべき変化。

---

## 6.3 reversal

方向転換。

例

* sentiment suddenly recovers
* risk trend turns downward
* fx trend reverses

意味

従来シナリオの見直し候補。

---

## 6.4 anomaly

通常範囲を超える異常。

例

* headline spike anomaly
* unusually high uncertainty
* abnormal market stress

意味

単純 trend では説明しきれない異常点。

---

## 6.5 regime_shift

状態の相転移。

例

* stable → tension
* tension → crisis
* crisis → de-escalation

意味

シナリオ構造そのものの見直しが必要。

---

## 6.6 volatility_expansion

不安定化の拡大。

例

* FX volatility expansion
* topic dispersion expansion
* sentiment dispersion expansion

意味

不確実性増大。

---

# 7. Signal Domains

Signal は複数ドメインで発生する。

## 7.1 Sentiment Signals

例

* persistent negative sentiment
* sudden uncertainty spike
* mixed sentiment instability

---

## 7.2 Topic Signals

例

* war topic surge
* energy disruption warning
* election instability signal

---

## 7.3 FX Signals

例

* JPY weakness warning
* THB instability warning
* USD shock signal

---

## 7.4 Composite Risk Signals

複数 Trend を統合した signal。

例

* geopolitical escalation warning
* energy shock warning
* financial stress warning

重要原則

```text
単一 trend signal
↓
複合 signal
```

の順で育てる。

---

# 8. Detection Principles

Signal は次の原則で検出する。

## 8.1 Not Every Trend Becomes a Signal

すべての Trend を signal にしない。

条件

* 継続性がある
* 強度が一定以上
* confidence が一定以上
* 人間にとって意味がある

---

## 8.2 Signal Requires Threshold

Signal にはしきい値が必要。

例

* strength >= 0.60
* confidence >= 0.55
* persistence >= 2 or 3 observations

数値は v1 では暫定でよい。
重要なのは

```text
しきい値を持つ
```

ことである。

---

## 8.3 Signal Must Be Explainable

Signal は理由を持つ。

最低限必要な説明

* どの trend から来たか
* なぜ signal 化されたか
* 何を警戒すべきか

重要原則

```text
説明できない signal は採用しない
```

---

## 8.4 Signal Is Warning, Not Decision

Signal は判断材料であり
最終決定ではない。

Signal が出ても

* 直ちに scenario を断定しない
* 直ちに prediction を固定しない
* Human の判断余地を残す

---

# 9. Signal Output Schema

Signal Layer の基本出力例

```json
{
  "date": "2026-03-09",
  "signals": [
    {
      "id": "energy_shock_warning",
      "type": "composite_risk",
      "level": "warning",
      "direction": "rising",
      "strength": 0.74,
      "confidence": 0.63,
      "derived_from": [
        "energy_topic_rising",
        "fx_volatility_rising"
      ],
      "summary": "Energy-related risk is rising with market instability.",
      "watchpoints": [
        "oil",
        "shipping",
        "middle_east"
      ]
    },
    {
      "id": "persistent_negative_sentiment",
      "type": "sentiment",
      "level": "guarded",
      "direction": "persistent",
      "strength": 0.61,
      "confidence": 0.58,
      "derived_from": [
        "sentiment_global_falling"
      ],
      "summary": "Negative sentiment remains elevated across recent observations.",
      "watchpoints": [
        "conflict_headlines",
        "risk_score"
      ]
    }
  ]
}
```

---

# 10. Required Fields

各 signal は最低限以下を持つ。

```text
id
type
level
direction
strength
confidence
derived_from
summary
watchpoints
```

意味

## id

signal の識別子

## type

signal 種別
例: sentiment / topic / fx / composite_risk

## level

警戒レベル
例: guarded / warning / elevated / critical

## direction

変化方向
例: rising / falling / persistent / reversal

## strength

signal 強度
0.0 – 1.0

## confidence

signal 信頼度
0.0 – 1.0

## derived_from

元になった trend id 一覧

## summary

人間が読める短い説明

## watchpoints

今後注視すべき観測点

---

# 11. Signal Level Semantics

Signal の警戒レベルは次を使う。

```text
guarded
warning
elevated
critical
```

意味

## guarded

注意して見る段階

## warning

明確な警告

## elevated

通常より高い警戒

## critical

危険水準

重要原則

```text
Signal level は UI色付けのためではなく
運用意味のために定義する
```

---

# 12. Relation to Scenario Layer

Scenario は Signal を材料にして未来分岐を作る。
Prediction Architecture でも Scenario Engine は `signal_latest.json` を入力に `scenario_latest.json` を出す。 

例

```text
Signal
energy_shock_warning
+
regime_shift_warning

↓
Scenario
middle_east_escalation
```

重要原則

```text
Signal なしの Scenario は弱い
```

これは Prediction Layer 設計原則とも一致する。 

---

# 13. Relation to Prediction Layer

Prediction は Signal を直接表示してもよいが、
Signal そのものは Prediction ではない。

Prediction は

* signal
* scenario
* confidence
* drivers
* watchpoints

を統合した **最終要約** である。 

重要原則

```text
Signal を Prediction の代用にしない
```

---

# 14. Relation to UI

UI は read-only であり、
signal の生成や再計算を行わない。 

UI 側で許可されるのは

* signal の表示
* signal list の並び替え
* signal level の可視化
* watchpoints の表示

禁止

* signal の自動補完
* signal strength の再計算
* derived_from の捏造
* scenario の代替生成

---

# 15. Integration with Morning Ritual

Signal Layer は Morning Ritual の一部として更新される。
理想的な日次処理は

```text
analysis build
↓
observation memory save
↓
trend build
↓
signal build
↓
scenario build
↓
prediction build
↓
prediction memory save
↓
prediction history index build
↓
UI update
```

である。 

重要原則

```text
Signal は日次心拍で更新される仮説の一部
```

---

# 16. v1 Implementation Plan

段階的に実装する。

## Phase 1

sentiment persistence
topic surge
fx instability

## Phase 2

acceleration
reversal
anomaly

## Phase 3

composite risk signals
regime shift signals

## Phase 4

historical analog linked signals
cross-domain signal fusion

---

# 17. Failure Modes to Avoid

避けるべき失敗

## Failure 1

```text
Trend をそのまま Signal と呼ぶ
```

## Failure 2

```text
1日だけの変化を signal 化する
```

## Failure 3

```text
説明のない signal
```

## Failure 4

```text
Signal から直接 Prediction を断定する
```

## Failure 5

```text
UI 側で signal を生成する
```

## Failure 6

```text
watchpoints を持たない signal
```

---

# 18. Long-Term Vision

Signal Layer は

GenesisPrediction における

```text
Early Warning Engine
```

となる。

役割

* 危険分岐の前兆を示す
* 人間に注視点を与える
* Scenario を強くする
* Prediction を説明可能にする

GenesisPrediction の目的は
正解を当てることではなく
**危険を早く知ること**である。 

---

# 19. Final Principle

Signal Layer の設計原則を一言で言うと

```text
Meaningful early warnings over raw trend movements
```

日本語では

```text
単なる変化より
意味のある危険信号を優先する
```

---

# 20. Final Summary

GenesisPrediction の Signal Layer は

```text
Trend
↓
Signal
↓
Scenario
```

の中央に位置する。

Signal は

* 流れの中の重要変化
* Early Warning
* Scenario の材料
* Prediction の説明材料

である。

Signal は決定ではない。
Signal は

```text
人間が先に気づくための警告
```

である。

---

END OF DOCUMENT

```
