# Scenario Engine
GenesisPrediction v2

Status: Active
Purpose: Signal を統合して未来分岐（Scenario）を生成する Scenario Engine の設計
Last Updated: 2026-03-07

---

# 0. Purpose

Scenario Engine は


Signal


を統合し、


未来分岐


を生成するエンジンである。

Trend Engine が


世界の流れ


を抽出し、

Signal Engine が


重要な兆候


を検出するのに対し、

Scenario Engine は


この先どう展開しうるか


を整理する。

目的

- 複数 Signal を統合する
- 将来の主要分岐を生成する
- best / base / worst の見通しを構造化する
- Prediction Engine の入力を生成する

---

# 1. Position in System

Prediction Layer の構造


Observation Memory
↓
Trend Engine
↓
Signal Engine
↓
Scenario Engine
↓
Prediction Engine


Scenario Engine は


未来分岐レイヤ


である。

---

# 2. Input

Scenario Engine は


signal_latest.json


を入力として使用する。

Signal Engine から渡される主な情報


signal type
domain
severity
confidence
duration
summary


複数 Signal を統合して、
将来シナリオを構築する。

---

# 3. Scenario Definition

Scenario は


未来の展開可能性


を意味する。

これは


単一の予言


ではない。

Scenario Engine は


複数の可能な未来


を並べる。

GenesisPrediction における基本形は


best_case
base_case
worst_case


である。

---

# 4. Core Scenario Types

Scenario Engine は最低限、以下の3系統を生成する。

---

## best_case

最も望ましい展開。

例


tension cools
risk fades
markets stabilize


---

## base_case

最も起こりやすい中心シナリオ。

例


elevated risk persists
limited deterioration
slow normalization


---

## worst_case

最も悪い方向への展開。

例


major escalation
market shock
broad instability


---

# 5. Scenario Construction Logic

Scenario Engine は
単一 Signal ではなく


Signal の組み合わせ


からシナリオを生成する。

考慮要素


signal count
signal severity
signal confidence
multi-domain alignment
persistence
conflict between signals


例

- sentiment persistence
- fx volatility expansion
- health deterioration
- geopolitical anomaly

これらが同時に存在する場合、


worst_case probability


は上がる。

---

# 6. Scenario Drivers

各 Scenario は


drivers


を持つ。

drivers は


そのシナリオを支える主要 Signal


である。

例

```json
[
  "negative sentiment persistence",
  "fx volatility expansion",
  "war coverage anomaly"
]

これにより Scenario は

説明可能

になる。

7. Scenario Probability

各 Scenario は

probability

を持つ。

範囲

0.0 ～ 1.0

基本ルール

best + base + worst = 1.0

probability は Signal 群から推定する

base_case は通常もっとも高い初期重みを持つ

強い複数 Signal があると worst_case が上昇する

改善方向 Signal が増えると best_case が上昇する

8. Scenario Confidence

Scenario 自体も

confidence

を持つ。

範囲

0.0 ～ 1.0

confidence は以下を反映する。

signal quality
cross-domain confirmation
data completeness
conflict level

例

複数ドメインで整合 → confidence 上昇

信号が弱くバラバラ → confidence 低下

9. Scenario Horizon

Scenario は horizon を持つ。

基本 horizon

3d
7d
30d

意味

3d = short-term

7d = tactical outlook

30d = structural outlook

重要原則

horizon ごとに Scenario は異なりうる

例

3d worst_case は高い

30d base_case は normalization

という形もありえる。

10. Scenario Fields

Scenario Engine が生成する各 Scenario の主要 field

name
horizon
probability
confidence
drivers
invalidation_conditions
summary
implications
watchpoints
11. Invalidation Conditions

Scenario には

invalidation_conditions

を持たせる。

これは

このシナリオが崩れる条件

である。

例

volatility drops below threshold

negative sentiment reverses

escalation-related coverage fades

これにより Scenario は

固定された物語

ではなく、

観測によって更新される仮説

になる。

12. Scenario Implications

Scenario は

implications

を持つ。

これは

そのシナリオが意味すること

である。

例

geopolitical risk remains elevated

remittance timing risk increases

safe-haven demand may strengthen

Prediction Engine はこの implications を要約して
最終予測を作る。

13. Scenario Output

Scenario Engine の出力

scenario_latest.json

保存先

analysis/prediction/
14. Example Output
{
  "as_of": "2026-03-07",
  "horizon": "7d",
  "scenarios": [
    {
      "name": "best_case",
      "probability": 0.18,
      "confidence": 0.56,
      "drivers": [
        "negative momentum easing",
        "volatility stabilization"
      ],
      "invalidation_conditions": [
        "renewed escalation headlines",
        "fx volatility spike"
      ],
      "implications": [
        "risk pressure softens",
        "market conditions stabilize"
      ],
      "watchpoints": [
        "war coverage volume",
        "usd/jpy volatility"
      ],
      "summary": "Tension cools and markets begin to stabilize."
    },
    {
      "name": "base_case",
      "probability": 0.57,
      "confidence": 0.71,
      "drivers": [
        "negative sentiment persistence",
        "elevated volatility",
        "continued risk headlines"
      ],
      "invalidation_conditions": [
        "clear risk reversal",
        "broad normalization in headlines"
      ],
      "implications": [
        "elevated risk persists",
        "caution remains warranted"
      ],
      "watchpoints": [
        "risk score trend",
        "headline persistence",
        "fx movement"
      ],
      "summary": "Elevated geopolitical tension persists without major escalation."
    },
    {
      "name": "worst_case",
      "probability": 0.25,
      "confidence": 0.64,
      "drivers": [
        "anomaly in war coverage",
        "fx volatility expansion",
        "risk acceleration"
      ],
      "invalidation_conditions": [
        "headline intensity fades",
        "volatility compresses quickly"
      ],
      "implications": [
        "market shock risk rises",
        "defensive positioning becomes more important"
      ],
      "watchpoints": [
        "breaking escalation news",
        "volatility breakout",
        "cross-domain stress"
      ],
      "summary": "A major escalation event drives broader instability and market stress."
    }
  ]
}
15. Scenario Selection Logic

Scenario Engine は

dominant scenario

を内部的に保持してもよい。

これは

最も確率が高いシナリオ

である。

ただし重要原則として、

dominant scenario = 唯一の未来

ではない。

Prediction Engine は dominant scenario を利用して
公開向け要約を生成するが、
best / base / worst 全体を保持する。

16. Multi-Domain Fusion

Scenario Engine の強みは

複数ドメイン統合

である。

対象例

world_politics
sentiment
fx
health
risk

単一ドメインだけでなく、

sentiment worsening

fx volatility rising

risk headlines increasing

が揃うと
Scenario の説得力が増す。

17. Scenario Conflict Handling

Signal は常に同じ方向とは限らない。

例

sentiment は悪化

FX は安定

health は改善

この場合、Scenario Engine は

conflict_level

を内部計算してよい。

原則

矛盾が大きい → confidence 低下

整合が高い → confidence 上昇

18. Scenario → Prediction Bridge

Scenario Engine の出力は

Prediction Engine

へ渡される。

Prediction Engine は

dominant scenario

overall risk

watchpoints

short summary

へ正規化する。

つまり

Scenario = 未来分岐
Prediction = 公開用要約

である。

19. Design Principles

Scenario Engine の原則

Principle 1

Scenario は

未来分岐

であり、

単一予言

ではない。

Principle 2

Scenario は

Signal の統合結果

である。

Principle 3

Scenario は

説明可能

でなければならない。

そのため drivers / invalidation_conditions を持つ。

Principle 4

Scenario は

更新可能な仮説

である。

Observation が変われば、Scenario も変わる。

Principle 5

Scenario は

Prediction より一段深い層

である。

UI は通常 Prediction を読むが、
将来的には Scenario UI を持ってもよい。

20. Future Expansion

将来追加予定

scenario trees
branching depth
historical analog scenarios
policy response scenarios
cross-market propagation scenarios

これにより
GenesisPrediction はより高度な

未来分岐エンジン

へ進化する。

21. Final Role

Scenario Engine は

GenesisPrediction の想像力

である。

役割

観測された兆候から
複数の未来を描く

その後

Prediction Engine

が

最終予測

として整理し、
UI と判断支援へ接続する。

END OF DOCUMENT