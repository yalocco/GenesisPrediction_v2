# Prediction Engine
GenesisPrediction v2

Status: Active
Purpose: Scenario を最終予測成果物へ正規化する Prediction Engine の設計
Last Updated: 2026-03-07

---

# 0. Purpose

Prediction Engine は


Scenario


を


最終予測成果物


へ変換するエンジンである。

Trend Engine が


世界の流れ


を抽出し、

Signal Engine が


重要な兆候


を検出し、

Scenario Engine が


複数の未来分岐


を生成するのに対し、

Prediction Engine は


人間とUIが読める最終予測


を作る。

目的

- Scenario を公開用の予測出力へ正規化する
- overall risk を決定する
- dominant scenario を選定する
- watchpoints を整理する
- UI / LABOS / report が読む統一フォーマットを定義する

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


Prediction Engine は


最終予測レイヤ


である。

---

# 2. Input

Prediction Engine は


scenario_latest.json


を入力として使用する。

主な入力要素


scenario name
probability
confidence
drivers
invalidation_conditions
implications
watchpoints
summary


Prediction Engine はこれらを要約し、


1つの公開用予測ビュー


へ変換する。

---

# 3. Prediction Definition

Prediction は


最終的な未来見通し


である。

ただし重要原則として、


Prediction = 単純な断言


ではない。

Prediction は


複数 Scenario を圧縮した公開用表現


である。

つまり


Scenario = 内部の未来分岐
Prediction = 外部向けの要約


である。

---

# 4. Core Role

Prediction Engine の中核役割は以下である。

- dominant scenario を選ぶ
- overall risk を決める
- confidence を集約する
- watchpoints を抽出する
- 予測 summary を作る
- 将来の判断支援へ接続する

---

# 5. Dominant Scenario

Prediction Engine は


dominant_scenario


を決定する。

定義


最も中心となるシナリオ


通常は

- probability が最大
- confidence が一定以上
- conflict が過大でない

という条件を満たすものを採用する。

重要原則


dominant_scenario = 唯一の未来


ではない。

dominant_scenario は
公開用要約の中心であり、
best / base / worst 全体は保持される。

---

# 6. Overall Risk

Prediction Engine は


overall_risk


を生成する。

標準ラベル


low
guarded
elevated
high
critical


決定要素

- worst_case probability
- base_case の risk tone
- signal severity
- cross-domain stress
- volatility
- anomaly presence

例

- best_case 優勢 → low / guarded
- base_case 優勢で緊張持続 → elevated
- worst_case 上昇 + anomaly 多発 → high / critical

---

# 7. Prediction Confidence

Prediction Engine は


confidence


を出力する。

範囲


0.0 ～ 1.0


confidence は以下を反映する。

- scenario confidence
- cross-domain confirmation
- signal consistency
- data completeness
- scenario conflict

原則

- 整合が高いほど上がる
- 矛盾が多いほど下がる
- データ欠損が大きいと下がる

---

# 8. Horizon

Prediction は horizon を持つ。

標準 horizon


3d
7d
30d


意味

- 3d = short-term alert
- 7d = tactical outlook
- 30d = structural outlook

Prediction Engine は horizon ごとに
別の prediction_latest を持ってもよいが、
当面は


7d


を基準の公開 horizon とする。

---

# 9. Watchpoints

Prediction Engine は


watchpoints


を出力する。

watchpoints とは


今後の予測を更新するために監視すべき項目


である。

例

- escalation headlines
- fx volatility breakout
- negative sentiment reversal
- health warn increase

watchpoints の役割

- 人間が何を見るべきか示す
- Morning Ritual 後のチェックポイントに使う
- 次回 Prediction 更新の観測対象になる

---

# 10. Implication Compression

Scenario Engine の


implications


は複数存在する。

Prediction Engine はそれを圧縮し、


summary


と


key_implications


へ変換してよい。

例

Scenario implications:

- geopolitical risk remains elevated
- remittance timing risk increases
- volatility may remain high

Prediction output:

- Risk remains elevated over the next 7 days.
- FX-sensitive decisions may require caution.

---

# 11. Prediction Fields

Prediction Engine が生成する主な field


as_of
horizon
overall_risk
confidence
dominant_scenario
scenario_probabilities
summary
key_implications
watchpoints
drivers
invalidation_conditions


補足

- `drivers` は dominant scenario の主要 driver を圧縮したもの
- `invalidation_conditions` は現予測が崩れる条件
- `scenario_probabilities` は best / base / worst の要約表示用

---

# 12. Prediction Output

Prediction Engine の出力


prediction_latest.json


保存先


analysis/prediction/


---

# 13. Example Output

```json
{
  "as_of": "2026-03-07",
  "horizon": "7d",
  "overall_risk": "elevated",
  "confidence": 0.69,
  "dominant_scenario": "base_case",
  "scenario_probabilities": {
    "best_case": 0.18,
    "base_case": 0.57,
    "worst_case": 0.25
  },
  "summary": "Risk remains elevated over the next 7 days as geopolitical tension persists without a confirmed major escalation.",
  "key_implications": [
    "Caution remains warranted in risk-sensitive decisions.",
    "FX volatility may remain elevated.",
    "Further escalation headlines could shift the outlook quickly."
  ],
  "watchpoints": [
    "breaking escalation news",
    "usd/jpy volatility breakout",
    "negative sentiment reversal",
    "cross-domain stress signals"
  ],
  "drivers": [
    "negative sentiment persistence",
    "continued risk headlines",
    "elevated volatility"
  ],
  "invalidation_conditions": [
    "headline intensity fades materially",
    "volatility compresses",
    "risk trend reverses"
  ]
}
14. Prediction Summary Style

Prediction Engine の summary は
以下の条件を満たすべきである。

短い

人間が読める

過剰断定しない

dominant scenario を反映する

risk tone が明確

良い例

Risk remains elevated over the next 7 days with persistent geopolitical stress.

避けるべき例

A war will definitely happen soon.

Prediction は

確率付きの見通し

であり、
断定予言ではない。

15. Invalidation Logic

Prediction Engine は

invalidation_conditions

を保持する。

これは

この予測が崩れる条件

である。

役割

予測の柔軟性を保つ

次回更新時の修正条件を明示する

prediction を固定断言にしない

例

volatility normalizes

sentiment reverses

escalation coverage fades

anomaly signal disappears

16. Scenario Compression Logic

Prediction Engine の本質は

Scenario compression

である。

圧縮対象

best / base / worst

drivers

implications

watchpoints

confidence

圧縮結果

prediction_latest.json

重要原則

情報を捨てるための圧縮

ではなく、

公開に適した形へ正規化するための圧縮

である。

内部の複雑さは Scenario に残し、
Prediction は読みやすさを優先する。

17. Prediction → UI Bridge

UI は通常、Prediction Engine の出力のみを読む。

正式参照先

analysis/prediction/prediction_latest.json

UI の役割

表示

のみ。

UI は

risk を再計算しない

scenario probability を再推論しない

summary を生成しない

既存原則どおり、

UI は read-only

である。

18. Prediction for LABOS / Reports

Prediction Engine の出力は
UI だけでなく以下にも利用できる。

LABOS public dashboard

daily digest

weekly outlook

alert notes

future decision support modules

Prediction Engine は

公開可能な最終形

を作る層であるため、
将来の外部提供でも重要になる。

19. Multi-Horizon Extension

将来は以下を同時生成してよい。

prediction_3d_latest.json
prediction_7d_latest.json
prediction_30d_latest.json

役割

3d = alert oriented

7d = tactical

30d = strategic

ただし v1 では複雑化を避けるため、

prediction_latest.json = 7d horizon

を標準とする。

20. Decision Support Bridge

Prediction Engine は
将来の

Decision Support AI

への橋渡し層である。

例

remittance caution

capital defense timing

portfolio hedging awareness

geopolitical alert escalation

ただし重要原則として、
Prediction Engine 自体は

判断そのもの

ではない。

Prediction Engine は

判断材料

を提供する。

判断は将来の別レイヤで行う。

21. Design Principles

Prediction Engine の原則

Principle 1

Prediction は

Scenario の公開用要約

である。

Principle 2

Prediction は

断定予言

ではない。

Principle 3

Prediction は

人間が読める

必要がある。

Principle 4

Prediction は

watchpoints

を必ず持つ。

未来を読むだけでなく、
何を見れば更新されるかを示す。

Principle 5

Prediction は

UI / LABOS / report 用の最終統一形式

である。

22. Future Expansion

将来追加予定

prediction deltas
daily prediction change log
confidence decomposition
scenario shift alerts
decision support hooks

これにより Prediction Engine は
より高度な

公開予測レイヤ

へ進化する。

23. Final Role

Prediction Engine は

GenesisPrediction の声

である。

Trend が変化を感じ取り、
Signal が兆候を検知し、
Scenario が複数の未来を描く。

Prediction Engine はそれを

人間が理解できる言葉

に変えて外へ出す。

役割

未来分岐を
最終予測へ整える

END OF DOCUMENT