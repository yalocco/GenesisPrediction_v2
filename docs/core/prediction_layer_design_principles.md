# Prediction Layer Design Principles
GenesisPrediction v2

Status: Active  
Purpose: GenesisPrediction v2 の Prediction Layer 設計原則を定義する  
Last Updated: 2026-03-19

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
- Prediction の explainability を構造として固定する
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

# 11. Explanation Is Part of Prediction Layer

GenesisPrediction において

```text
Explanation
```

は独立した真実層ではない。

Explanation は

```text
Signal / Scenario / Prediction / FX Decision
```

などの判断結果を

```text
人間が理解可能な構造
```

へ変換するための説明層である。

重要原則

```text
Explanation は新しい真実を作らない
```

Explanation が扱うものは

* なぜその Prediction なのか
* なぜその Scenario なのか
* なぜその Signal なのか
* なぜその FX 判断なのか
* 世界で何が起きているのか

である。

ただしそれは

```text
analysis に存在する既存の判断結果
```

を言語化・構造化するものであり、
元の判断ロジックを置き換えるものではない。

---

# 12. Explanation Layer Position

実装上の流れは以下である。

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
↓
Explanation
↓
UI
```

ただし意味上は

```text
Explanation = 公開用説明構造
```

であり、

```text
Prediction の下位本体
```

ではない。

重要なのは

```text
説明は後段であって
判断の代替ではない
```

ということである。

---

# 13. Explanation Structure, Not Free Generation

GenesisPrediction の説明は

```text
自由作文
```

ではなく

```text
構造
```

として定義する。

理由

* UI 側で説明を再生成させないため
* 説明品質を安定させるため
* 予測ロジックと説明ロジックを分離するため
* 多言語化時に意味を保ったまま展開しやすくするため

重要原則

```text
説明は生成ではなく構造として定義する
```

---

# 14. UI Must Not Compute Meaning

UI は表示のみを担当する。

UI がやってよいこと

* explanation artifact を読む
* headline を表示する
* summary を表示する
* drivers / watchpoints / invalidation を表示する
* 用語 tooltip を出す
* detail panel に説明を出す

UI がやってはいけないこと

* prediction から explanation を再推論する
* signal の意味を UI 側で再定義する
* confidence の意味を勝手に解釈する
* FX reason を UI 側で作文する
* 日付決定や判定ロジックを持つ

重要原則

```text
UI は意味を計算しない
```

---

# 15. Explanation Artifacts

Prediction Layer の explainability を支える最小 artifact 例は以下である。

```text
analysis/explanation/

prediction_explanation_latest.json
scenario_explanation_latest.json
signal_explanation_latest.json
fx_explanation_latest.json
world_explanation_latest.json
```

役割

## prediction_explanation_latest.json

なぜその Prediction なのかを説明する

## scenario_explanation_latest.json

なぜその未来分岐なのかを説明する

## signal_explanation_latest.json

なぜその Signal が立っているのかを説明する

## fx_explanation_latest.json

なぜその FX 判断なのかを説明する

## world_explanation_latest.json

世界で今何が起きているのかを要約する

重要原則

```text
説明も artifact として固定する
```

---

# 16. Common Explanation Schema

Phase1 における説明 artifact は
まず共通骨格を持つべきである。

最小 schema 例

```json
{
  "as_of": "YYYY-MM-DD",
  "subject": "prediction | scenario | signal | fx | world",
  "status": "ok | unavailable",
  "headline": "短い一文",
  "summary": "人間向けの要約",
  "why_it_matters": "なぜ重要か",
  "based_on": [
    "参照artifactや主要要因"
  ],
  "drivers": [
    "主要要因"
  ],
  "watchpoints": [
    "今後の注視点"
  ],
  "invalidation": [
    "見直し条件"
  ],
  "must_not_mean": [
    "誤解してはいけない意味"
  ],
  "ui_terms": [
    {
      "term": "confidence",
      "meaning": "この文脈での意味"
    }
  ]
}
```

重要原則

```text
まず骨格を固定し
文章美より意味の整合性を優先する
```

---

# 17. Must-Not-Mean Principle

説明では

```text
何を意味するか
```

だけでなく

```text
何を意味しないか
```

も持つべきである。

理由

* UI 利用者の誤読を防ぐ
* confidence の誤解を防ぐ
* risk 表示の過剰解釈を防ぐ
* prediction を断定未来と誤認させないため

例

```text
confidence は的中率ではない
prediction は確定未来ではない
watchpoint は確定警報ではない
```

重要原則

```text
説明は誤解防止まで含めて設計する
```

---

# 18. Prediction Supports Humans

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

# 19. Layer Responsibilities

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

## Explanation

判断結果を人間可読の構造へ変換する

重要原則

```text
各層の責務を混ぜない
```

---

# 20. Minimal Output by Layer

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

## Explanation

```text
prediction_explanation_latest.json
scenario_explanation_latest.json
signal_explanation_latest.json
fx_explanation_latest.json
world_explanation_latest.json
```

例

```text
headline
summary
why_it_matters
drivers
watchpoints
invalidation
must_not_mean
ui_terms
```

---

# 21. Failure Modes to Avoid

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

## Failure 7

```text
UI側で explanation を作文する
```

## Failure 8

```text
explanation が元artifactと矛盾する
```

## Failure 9

```text
must_not_mean を持たず誤解を放置する
```

---

# 22. Integration with Morning Ritual

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
explanation build
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

# 23. Role of Confidence

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

# 24. Role of Watchpoints

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

# 25. GenesisPrediction-Specific Goal

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

# 26. Final Design Principle

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

# 27. Final Summary

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
↓
Explanation
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

そして Explanation は

```text
その判断結果を
人間が理解可能な構造へ変換する公開用説明層
```

である。

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

```
