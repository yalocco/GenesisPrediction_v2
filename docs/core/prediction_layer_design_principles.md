# Prediction Layer Design Principles
GenesisPrediction v2

Status: Active  
Purpose: GenesisPrediction v2 の Prediction Layer 設計原則を定義する  
Last Updated: 2026-03-08

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 における

Prediction Layer

の設計原則を定義する。

目的

- 予測エンジン設計の判断軸を固定する
- 未来予測を “当てもの” にしない
- Observation / Trend / Signal / Scenario / Prediction の責務を分離する
- 将来の Prediction System 強化時に構造破壊を防ぐ

---

# 1. Core Principle

Prediction Layer の最重要原則はこれである。

```text
Prediction を主役にしない
````

GenesisPrediction において主役は

```text
Observation
↓
Trend
↓
Signal
↓
Scenario
```

であり、

```text
Prediction
```

はその最終要約である。

---

# 2. Why Prediction-First Fails

悪い構造

```text
news / sentiment / fx
↓
prediction
```

この構造は以下の問題を生む。

* 理由が見えない
* 外れた時に原因分析できない
* 説明不能な予測になる
* AIがそれらしい言葉を出すだけになる
* システム改善点が不明になる

つまり

```text
観測から直接予測
```

は失敗しやすい。

---

# 3. Correct Prediction Structure

GenesisPrediction の正しい構造は以下である。

```text
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

意味

## Observation

世界を観測する

## Trend

変化の方向を抽出する

## Signal

重要な兆候を検出する

## Scenario

未来分岐を整理する

## Prediction

公開用の最終要約を生成する

---

# 4. Prediction Is the Last Layer

Prediction は本体ではない。

Prediction は

```text
最終表示
最終要約
公開用サマリー
```

である。

本体はむしろ

```text
Trend
Signal
Scenario
```

にある。

したがって

```text
Prediction Engine を先に賢くしようとしない
```

ことが重要である。

---

# 5. Observation First

Prediction は必ず

```text
観測
```

の上に立つ。

GenesisPrediction の観測入力例

```text
daily_summary_latest.json
sentiment_latest.json
health_latest.json
fx inputs
observation artifacts
```

重要原則

```text
Prediction は観測のない場所から生まれない
```

---

# 6. Memory Is Required

Prediction は latest だけでは弱い。

必要構造

```text
analysis/latest
↓
history
↓
trend
↓
signal
↓
scenario
↓
prediction
```

これにより

```text
変化の継続
方向性
異常
加速
反転
```

を扱えるようになる。

重要原則

```text
Memory is intelligence
```

---

# 7. Trend Before Signal

Signal は単独では生成しない。

まず Trend を抽出する。

例

```text
risk rising
uncertainty rising
mixed sentiment persistent
fx instability
confidence falling
```

Trend の役割は

```text
流れ
```

を示すことである。

Signal は

```text
その流れの中で注意すべき変化
```

である。

---

# 8. Signal Before Scenario

Signal は

```text
兆候
```

であり、

Scenario は

```text
未来分岐
```

である。

Signal 例

```text
persistence
acceleration
anomaly
regime_shift
volatility_expansion
reversal
```

Scenario は Signal をもとに生成される。

重要原則

```text
Signal なしの Scenario は弱い
```

---

# 9. Scenario Is Mandatory

GenesisPrediction では

```text
単一未来
```

を前提としない。

必ず

```text
best_case
base_case
worst_case
```

のような

```text
未来分岐
```

を持つ。

理由

* 未来は一本線ではない
* 不確実性を含む方が正しい
* 判断支援に必要なのは分岐理解である
* 当てることより外れ方を管理する方が重要である

重要原則

```text
Scenario を挟まない Prediction は危険
```

---

# 10. Prediction Must Be Explainable

Prediction は必ず説明可能でなければならない。

最低限必要な要素

```text
summary
drivers
watchpoints
confidence
invalidation_conditions
```

意味

## summary

予測の要約

## drivers

その予測を支える要因

## watchpoints

今後注視すべき点

## confidence

予測に対する確信度

## invalidation_conditions

何が起きたら予測を見直すべきか

重要原則

```text
理由のない予測は採用しない
```

---

# 11. Prediction Supports Humans

Prediction Layer の目的は

```text
未来を断言すること
```

ではない。

目的は

```text
危険分岐を早く見せること
```

である。

GenesisPrediction の Prediction は

```text
判断支援
```

のために存在する。

最終決定は

```text
Human
```

が行う。

---

# 12. Layer Responsibilities

Prediction Layer の責務分離

## Observation

観測データを揃える

## Trend

変化の方向を抽出する

## Signal

注意すべき兆候を検出する

## Scenario

未来分岐を整理する

## Prediction

公開用サマリーを出す

重要原則

```text
各層の責務を混ぜない
```

---

# 13. Minimal Output by Layer

各層の最低出力例

## Trend

```text
trend_latest.json
```

例

```text
risk trend
sentiment trend
confidence trend
fx trend
```

## Signal

```text
signal_latest.json
```

例

```text
persistence
anomaly
reversal
acceleration
regime_shift
```

## Scenario

```text
scenario_latest.json
```

例

```text
best_case
base_case
worst_case
probabilities
drivers
watchpoints
```

## Prediction

```text
prediction_latest.json
```

例

```text
overall_risk
dominant_scenario
confidence
summary
watchpoints
drivers
```

---

# 14. Failure Modes to Avoid

Prediction Layer 設計で避けるべき失敗

## Failure 1

```text
Observation から直接 Prediction
```

## Failure 2

```text
Scenario を持たない単一未来
```

## Failure 3

```text
confidence だけ高く見せる
```

## Failure 4

```text
理由のない risk 判定
```

## Failure 5

```text
UI側で予測ロジックを持つ
```

## Failure 6

```text
history を使わず latest のみで判断する
```

---

# 15. Integration with Morning Ritual

Prediction Layer は

```text
Morning Ritual
```

の一部として更新される。

理想的な流れ

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

重要原則

```text
Prediction は日次心拍で更新される仮説
```

---

# 16. Role of Confidence

confidence は

```text
当たる確率
```

ではなく、

```text
現在の観測とシナリオ整合性の強さ
```

として扱う。

つまり

* データの十分性
* trend の明瞭さ
* signal の強さ
* scenario の整合性

を反映する。

重要原則

```text
confidence を飾りにしない
```

---

# 17. Role of Watchpoints

watchpoints は Prediction Layer において非常に重要である。

watchpoints は

```text
未来を変える観測点
```

である。

役割

* シナリオ更新条件を示す
* Human に注視点を与える
* Prediction の運用可能性を上げる

重要原則

```text
Prediction は watchpoints を持つべきである
```

---

# 18. GenesisPrediction-Specific Goal

GenesisPrediction における Prediction Layer の目的は

```text
正解を当てること
```

ではなく

```text
危険を早く知ること
```

である。

したがって Prediction は

```text
危険分岐の整理
リスクの見える化
判断支援
```

を優先する。

---

# 19. Final Design Principle

Prediction Layer の設計原則を一言で言うと

```text
Explainable branching over single-shot prediction
```

日本語では

```text
単発予測より
説明可能な未来分岐を優先する
```

である。

---

# 20. Final Summary

GenesisPrediction の Prediction Layer は

```text
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

で構成される。

重要なのは

```text
Prediction を主役にしない
```

ことである。

主役は

```text
Observation
Trend
Signal
Scenario
```

であり、

Prediction はその最終要約に過ぎない。

これを守ることで、
GenesisPrediction は

```text
当てものAI
```

ではなく

```text
危険を早く知るための説明可能な予測AI
```

として進化できる。

---

END OF DOCUMENT

````
