# Prediction Data Schema
GenesisPrediction v2

Status: Active  
Purpose: Signal / Scenario / Prediction の正式データ構造を定義する  
Last Updated: 2026-03-09

---

# 1. Purpose

本ドキュメントは、Prediction Layer の runtime output schema を固定する。

対象:

```text
analysis/prediction/signal_latest.json
analysis/prediction/scenario_latest.json
analysis/prediction/prediction_latest.json
analysis/prediction/history/YYYY-MM-DD/prediction.json
```

目的:

- Signal / Scenario / Prediction の責務を明確にする
- Morning Ritual / scripts / UI / history 保存の整合を固定する
- UI が field 名を毎回推測しなくて済むようにする
- Early Warning Engine の出力を安定させる

重要原則:

```text
analysis = Single Source of Truth
UI = read-only
Prediction = 最終要約
```

---

# 2. Layer Boundary

Prediction Layer の正式な流れ:

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

各 layer の役割:

```text
Signal     = 注意すべき兆候
Scenario   = 未来分岐
Prediction = 公開用の最終要約
```

禁止事項:

```text
Prediction が Signal / Scenario の役割を兼務しない
UI が risk / probability / confidence を再計算しない
history 表示のために latest を改変しない
```

---

# 3. Storage Layout

Prediction Layer の標準保存場所:

```text
analysis/prediction/
  signal_latest.json
  scenario_latest.json
  prediction_latest.json
  history/
    YYYY-MM-DD/
      prediction.json
```

補足:

- `signal_latest.json` は Signal Engine の最新出力
- `scenario_latest.json` は Scenario Engine の最新出力
- `prediction_latest.json` は Prediction Engine の最新出力
- `history/YYYY-MM-DD/prediction.json` は当日の prediction snapshot
- v1 では history の正式凍結対象は prediction を主とする

---

# 4. Common Root Fields

Signal / Scenario / Prediction すべてに共通して持つことが望ましい field:

```text
version
as_of
generated_at
source_layer
horizon_days
schema_name
schema_version
```

意味:

## version

ドキュメント自体の出力 version。

例:

```text
v1
v1.0
```

## as_of

この予測スナップショットが対象とする基準日。

形式:

```text
YYYY-MM-DD
```

## generated_at

生成日時。

形式:

```text
ISO 8601 UTC
```

## source_layer

どの layer の成果物か。

例:

```text
signal
scenario
prediction
```

## horizon_days

予測 horizon 日数。

v1 標準:

```text
7
```

## schema_name

schema 識別名。

例:

```text
genesis_signal_schema
genesis_scenario_schema
genesis_prediction_schema
```

## schema_version

schema version。

例:

```text
1.0
```

---

# 5. Signal Schema

ファイル:

```text
analysis/prediction/signal_latest.json
```

Signal は Early Warning のための兆候出力である。

## 5.1 Root Structure

標準 root:

```text
version
schema_name
schema_version
source_layer
as_of
generated_at
horizon_days
overall_signal_level
signal_count
early_warning_active
signals[]
summary
notes
```

## 5.2 Root Field Definitions

### overall_signal_level

全体の signal 強度。

例:

```text
low
moderate
elevated
high
critical
```

### signal_count

検出された signal 数。

型:

```text
integer
```

### early_warning_active

Early Warning Engine が発火しているか。

型:

```text
boolean
```

### summary

その日の signal 状況の短い要約。

### notes

補足説明。省略可。

## 5.3 signals[] Structure

各 signal item は少なくとも以下を持つ:

```text
id
name
type
level
score
status
direction
description
evidence
drivers
watchpoints
invalidation_conditions
related_trends
related_observations
confidence
```

## 5.4 Signal Item Definitions

### id

一意 ID。

例:

```text
sig_2026-03-09_001
```

### name

signal 名。

例:

```text
risk_acceleration
regime_shift_warning
volatility_expansion
```

### type

signal 種別。

例:

```text
persistence
acceleration
reversal
anomaly
regime_shift
volatility_expansion
```

### level

signal の重要度。

例:

```text
low
moderate
elevated
high
critical
```

### score

signal 強度の数値表現。

推奨:

```text
0.0 - 1.0
```

### status

現在の状態。

例:

```text
active
watch
cooling
resolved
```

### direction

変化方向。

例:

```text
rising
falling
stable
accelerating
reversing
```

### description

人間可読の説明。

### evidence

signal 判定根拠。配列推奨。

例:

```text
trend persistence for 3 days
headline intensity rising
fx volatility expanding
```

### drivers

signal を支える要因。

型:

```text
string[]
```

### watchpoints

継続監視点。

型:

```text
string[]
```

### invalidation_conditions

この signal を弱める / 無効化する条件。

型:

```text
string[]
```

### related_trends

関連する trend 名や ID。

### related_observations

関連する observation source や概念。

### confidence

この signal 自体の信頼度。

推奨:

```text
0.0 - 1.0
```

## 5.5 Signal Example

```json
{
  "version": "v1",
  "schema_name": "genesis_signal_schema",
  "schema_version": "1.0",
  "source_layer": "signal",
  "as_of": "2026-03-09",
  "generated_at": "2026-03-09T03:10:00Z",
  "horizon_days": 7,
  "overall_signal_level": "elevated",
  "signal_count": 2,
  "early_warning_active": true,
  "summary": "Risk acceleration and regime shift warning are active.",
  "signals": [
    {
      "id": "sig_2026-03-09_001",
      "name": "risk_acceleration",
      "type": "acceleration",
      "level": "high",
      "score": 0.78,
      "status": "active",
      "direction": "accelerating",
      "description": "Headline risk and market stress are rising together.",
      "evidence": [
        "risk trend rising for 3 days",
        "headline intensity increasing",
        "fx volatility expanding"
      ],
      "drivers": [
        "persistent geopolitical tension",
        "cross-market uncertainty"
      ],
      "watchpoints": [
        "new escalation headlines",
        "sharp fx move"
      ],
      "invalidation_conditions": [
        "headline intensity cools",
        "volatility normalizes"
      ],
      "related_trends": [
        "risk_trend",
        "fx_volatility"
      ],
      "related_observations": [
        "daily_summary_latest",
        "sentiment_latest"
      ],
      "confidence": 0.74
    }
  ]
}
```

---

# 6. Scenario Schema

ファイル:

```text
analysis/prediction/scenario_latest.json
```

Scenario は signal を未来分岐へ変換した出力である。

## 6.1 Root Structure

標準 root:

```text
version
schema_name
schema_version
source_layer
as_of
generated_at
horizon_days
scenario_count
dominant_scenario
scenario_set
summary
scenarios
watchpoints
notes
```

## 6.2 Root Field Definitions

### scenario_count

生成された scenario 数。

v1 推奨:

```text
3
```

### dominant_scenario

現時点で最も有力な scenario 名。

通常:

```text
best_case
base_case
worst_case
```

### scenario_set

採用している scenario セット名。

例:

```text
best_base_worst_v1
```

### summary
n
scenario 全体の短い要約。

### scenarios

scenario 本体。v1 では object 形式を標準とする。

```text
scenarios.best_case
scenarios.base_case
scenarios.worst_case
```

### watchpoints

全 scenario 横断で重要な watchpoints。

型:

```text
string[]
```

## 6.3 Scenario Item Structure

各 scenario は少なくとも以下を持つ:

```text
name
label
probability
confidence
risk_level
summary
description
drivers
watchpoints
invalidation_conditions
implications
trigger_signals
```

## 6.4 Scenario Item Definitions

### name

正式名。

例:

```text
best_case
base_case
worst_case
```

### label

表示用ラベル。

例:

```text
Best Case
Base Case
Worst Case
```

### probability

scenario の相対確率。

推奨:

```text
0.0 - 1.0
```

補足:

- v1 では合計 1.0 を推奨
- 将来、非正規化 score 型へ拡張してもよいが、その場合は schema version を上げる

### confidence

その scenario 記述への信頼度。

### risk_level

scenario が意味するリスク水準。

例:

```text
low
moderate
elevated
high
critical
```

### summary

1行要約。

### description

少し長めの説明。

### drivers

scenario を成立させる要因。

### watchpoints

この scenario の継続観察項目。

### invalidation_conditions

この scenario を崩す条件。

### implications

想定される意味・影響。

### trigger_signals

この scenario に影響した signal ID or signal 名。

## 6.5 Scenario Example

```json
{
  "version": "v1",
  "schema_name": "genesis_scenario_schema",
  "schema_version": "1.0",
  "source_layer": "scenario",
  "as_of": "2026-03-09",
  "generated_at": "2026-03-09T03:12:00Z",
  "horizon_days": 7,
  "scenario_count": 3,
  "dominant_scenario": "base_case",
  "scenario_set": "best_base_worst_v1",
  "summary": "Base case remains dominant, but worst-case probability is elevated.",
  "watchpoints": [
    "escalation headlines",
    "fx stress persistence",
    "negative sentiment clustering"
  ],
  "scenarios": {
    "best_case": {
      "name": "best_case",
      "label": "Best Case",
      "probability": 0.18,
      "confidence": 0.56,
      "risk_level": "moderate",
      "summary": "Tensions cool and volatility fades.",
      "description": "Recent risk signals fade without regime break.",
      "drivers": [
        "headline cooling",
        "volatility normalization"
      ],
      "watchpoints": [
        "de-escalation signs",
        "risk trend flattening"
      ],
      "invalidation_conditions": [
        "new escalation cluster",
        "sudden market shock"
      ],
      "implications": [
        "lower short-term stress",
        "reduced alert posture"
      ],
      "trigger_signals": [
        "risk_acceleration"
      ]
    },
    "base_case": {
      "name": "base_case",
      "label": "Base Case",
      "probability": 0.52,
      "confidence": 0.68,
      "risk_level": "elevated",
      "summary": "Tension persists without full escalation.",
      "description": "Current stress regime continues with intermittent flare-ups.",
      "drivers": [
        "persistent uncertainty",
        "ongoing volatility"
      ],
      "watchpoints": [
        "3-day risk persistence",
        "sentiment deterioration"
      ],
      "invalidation_conditions": [
        "clear improvement in trend cluster",
        "volatility compression"
      ],
      "implications": [
        "continued caution",
        "elevated monitoring"
      ],
      "trigger_signals": [
        "risk_acceleration",
        "regime_shift_warning"
      ]
    },
    "worst_case": {
      "name": "worst_case",
      "label": "Worst Case",
      "probability": 0.30,
      "confidence": 0.64,
      "risk_level": "high",
      "summary": "Escalation broadens and stress regime deepens.",
      "description": "Existing warning signals compound into broader instability.",
      "drivers": [
        "escalation cascade",
        "cross-market contagion"
      ],
      "watchpoints": [
        "multi-day headline shock",
        "fx volatility spike"
      ],
      "invalidation_conditions": [
        "rapid de-escalation",
        "shock absorption without follow-through"
      ],
      "implications": [
        "higher risk posture",
        "need for tighter review"
      ],
      "trigger_signals": [
        "risk_acceleration",
        "regime_shift_warning"
      ]
    }
  }
}
```

---

# 7. Prediction Schema

ファイル:

```text
analysis/prediction/prediction_latest.json
```

Prediction は Scenario の公開用最終要約である。

## 7.1 Root Structure

標準 root:

```text
version
schema_name
schema_version
source_layer
as_of
generated_at
horizon_days
overall_risk
dominant_scenario
confidence
summary
signal_count
early_warning_active
best_case
base_case
worst_case
scenarios
drivers
watchpoints
invalidation
implications
notes
```

## 7.2 Root Field Definitions

### overall_risk

その日の総合リスク評価。

例:

```text
low
moderate
elevated
high
critical
```

### dominant_scenario

最も有力な scenario 名。

### confidence

Prediction 全体への信頼度。

推奨:

```text
0.0 - 1.0
```

### summary

最重要の人間可読要約。

### signal_count

Prediction に反映された signal 数。

### early_warning_active

Early Warning 発火状態。

### best_case / base_case / worst_case

UI と history 互換性のための shortcut field。

推奨値:

```text
scenario summary text
```

または

```text
scenario label
```

ただし v1 では summary text を推奨する。

### scenarios

Prediction page が参照する scenario 情報。

推奨:

```text
scenarios.best
scenarios.base
scenarios.worst
```

各 node は少なくとも以下を持つ:

```text
name
probability
risk_level
summary
confidence
```

### drivers

Prediction 全体を支える主要 drivers。

### watchpoints

Prediction UI と Early Warning UI が共有できる監視点。

### invalidation

Prediction 仮説を崩す条件。

型:

```text
string[]
```

### implications

判断支援上の意味。

## 7.3 Prediction Example

```json
{
  "version": "v1",
  "schema_name": "genesis_prediction_schema",
  "schema_version": "1.0",
  "source_layer": "prediction",
  "as_of": "2026-03-09",
  "generated_at": "2026-03-09T03:15:00Z",
  "horizon_days": 7,
  "overall_risk": "elevated",
  "dominant_scenario": "base_case",
  "confidence": 0.69,
  "summary": "Base case remains dominant over 7 days, but worst-case probability is elevated enough to keep early warning active.",
  "signal_count": 2,
  "early_warning_active": true,
  "best_case": "Tensions cool and volatility fades.",
  "base_case": "Tension persists without full escalation.",
  "worst_case": "Escalation broadens and stress regime deepens.",
  "scenarios": {
    "best": {
      "name": "best_case",
      "probability": 0.18,
      "risk_level": "moderate",
      "summary": "Tensions cool and volatility fades.",
      "confidence": 0.56
    },
    "base": {
      "name": "base_case",
      "probability": 0.52,
      "risk_level": "elevated",
      "summary": "Tension persists without full escalation.",
      "confidence": 0.68
    },
    "worst": {
      "name": "worst_case",
      "probability": 0.30,
      "risk_level": "high",
      "summary": "Escalation broadens and stress regime deepens.",
      "confidence": 0.64
    }
  },
  "drivers": [
    "persistent geopolitical tension",
    "cross-market uncertainty",
    "volatility expansion"
  ],
  "watchpoints": [
    "new escalation headlines",
    "fx stress persistence",
    "negative sentiment clustering"
  ],
  "invalidation": [
    "headline intensity cools",
    "volatility normalizes",
    "risk trend flattens"
  ],
  "implications": [
    "maintain elevated monitoring",
    "prepare for scenario drift review"
  ]
}
```

---

# 8. History Snapshot Schema

ファイル:

```text
analysis/prediction/history/YYYY-MM-DD/prediction.json
```

history snapshot は `prediction_latest.json` の日次凍結版である。

重要原則:

```text
history = review source
latest = current source
```

## 8.1 History Minimum Fields

Prediction History UI 互換のため、少なくとも以下を保持する:

```text
as_of
overall_risk
dominant_scenario
confidence
best_case
base_case
worst_case
watchpoints
summary
```

## 8.2 Recommended Rule

history は可能な限り latest prediction root をそのまま保存する。

理由:

- schema 差分事故を減らせる
- review / drift 比較が容易
- UI 互換を保ちやすい

---

# 9. UI Compatibility Rules

Prediction UI の正式 source:

```text
analysis/prediction/prediction_latest.json
```

Prediction History UI の正式 source:

```text
analysis/prediction/history/*/prediction.json
```

UI 互換のための必須方針:

## Prediction Page

最低限これを読めること:

```text
as_of
horizon_days
overall_risk
dominant_scenario
summary
confidence
signal_count
watchpoints[]
drivers[]
invalidation[]
implications[]
```

## Prediction Scenario Display

UI は次のどちらでも扱えるようにしてよい:

```text
best_case / base_case / worst_case
```

または

```text
scenarios.best / scenarios.base / scenarios.worst
```

ただし runtime の正式 schema は本ドキュメントを正とする。

## No Recalculation Rule

UI は以下をしてはならない:

```text
probability 再計算
confidence 再推定
overall_risk 独自判定
scenario rank 再評価
```

---

# 10. Runtime Validation Rules

Signal / Scenario / Prediction を出力する runtime は、最低限次を満たすこと。

## 10.1 Signal Validation

```text
signals[] exists
signal_count == len(signals)
overall_signal_level exists
early_warning_active exists
```

## 10.2 Scenario Validation

```text
scenarios.best_case exists
scenarios.base_case exists
scenarios.worst_case exists
dominant_scenario exists
scenario_count >= 3
```

推奨:

```text
probability sum ≈ 1.0
```

## 10.3 Prediction Validation

```text
overall_risk exists
dominant_scenario exists
confidence exists
summary exists
watchpoints exists
```

## 10.4 History Validation

```text
history snapshot must include as_of
history snapshot must include dominant_scenario
history snapshot must include confidence
```

---

# 11. Failure Safety

schema 不整合時の原則:

## runtime side

```text
不完全な prediction を黙って publish しない
必須 field 欠落時は warning / failure を明示する
history へ壊れた snapshot を保存しない
```

## UI side

```text
core prediction content に fallback 捏造をしない
history が無ければ empty state を出す
missing field は unavailable 表示に留める
```

---

# 12. v1 Required Fields Summary

v1 で最低限固定したい field をまとめる。

## signal_latest.json

```text
as_of
generated_at
horizon_days
overall_signal_level
signal_count
early_warning_active
signals[]
summary
```

## scenario_latest.json

```text
as_of
generated_at
horizon_days
scenario_count
dominant_scenario
summary
scenarios.best_case
scenarios.base_case
scenarios.worst_case
watchpoints[]
```

## prediction_latest.json

```text
as_of
generated_at
horizon_days
overall_risk
dominant_scenario
confidence
summary
signal_count
early_warning_active
best_case
base_case
worst_case
scenarios
drivers[]
watchpoints[]
invalidation[]
implications[]
```

## history/YYYY-MM-DD/prediction.json

```text
as_of
overall_risk
dominant_scenario
confidence
best_case
base_case
worst_case
watchpoints[]
summary
```

---

# 13. Future Expansion

将来追加してよい field:

```text
regime
regime_score
scenario_tree
analog_matches
review_notes
drift_vs_yesterday
confidence_components
risk_components
source_refs
```

ただし原則:

```text
追加はよい
既存 core field を壊さない
UI 後方互換を意識する
schema_version を上げる
```

---

# 14. Final Principle

Prediction Data Schema の核心はこれである。

```text
Signal は兆候
Scenario は未来分岐
Prediction は最終要約
```

そして

```text
analysis が真実
UI は表示のみ
Prediction は判断支援であり決定そのものではない
```

この schema は、Morning Ritual・Prediction Runtime・Prediction UI・Prediction History の共通土台である。

---

END OF DOCUMENT
