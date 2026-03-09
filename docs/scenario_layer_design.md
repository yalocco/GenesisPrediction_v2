# Scenario Layer Design
GenesisPrediction v2

Status: Active  
Purpose: GenesisPrediction v2 の Scenario Layer を定義する  
Last Updated: 2026-03-09

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 における

```text
Scenario Layer
```

の設計を定義する。

目的

- Signal から未来分岐を生成する構造を固定する
- Early Warning Engine に必要な分岐思考を導入する
- Prediction を単発出力ではなく説明可能な最終要約にする
- Scenario Engine の責務を Signal / Prediction と分離する
- 将来の multi-horizon / scenario tree 拡張に耐える基盤を作る

---

# 1. Core Principle

Scenario Layer の最重要原則はこれである。

```text
Scenario は未来を断言しない
Scenario は未来分岐を整理する
```

GenesisPrediction は

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

という構造を持つ。

この中で Scenario の役割は

```text
Signal から複数の合理的な未来分岐を作ること
```

である。

Prediction のように一本の公開要約を出す層ではない。

---

# 2. Why Scenario Layer Is Necessary

Scenario Layer を省略すると、

```text
Signal
↓
Prediction
```

となり、次の問題が起こる。

- 単一未来に見えてしまう
- 不確実性が見えない
- 外れた時にどの分岐を見落としたか検証できない
- Human が備えるべき watchpoint を整理できない
- Prediction が「それっぽい断言」に劣化する

GenesisPrediction の目的は

```text
未来を当てること
```

ではなく

```text
危険を早く知ること
```

であるため、Scenario Layer は必須である。 fileciteturn0file35

---

# 3. Position in Prediction Layer

Scenario Layer は Prediction Layer の第4層である。

```text
Observation = 観測
Trend       = 流れ
Signal      = 兆候
Scenario    = 未来分岐
Prediction  = 最終要約
```

Prediction Layer 全体の責務分離は

```text
Prediction を主役にしない
```

という原則に従う。 fileciteturn0file35

つまり Scenario は

```text
Prediction の前提条件
```

であり、Prediction よりも本体側に近い。

---

# 4. Scenario Layer Responsibility

Scenario Layer の責務は次の5つである。

## 4.1 Signal を未来分岐へ変換する

Signal は兆候であり、まだ未来そのものではない。

Scenario Layer は

```text
persistence
acceleration
reversal
anomaly
regime_shift
volatility_expansion
```

などの Signal を、

```text
今後どう展開し得るか
```

という分岐へ変換する。 Signal は Scenario の入力として位置づけられている。 fileciteturn0file35turn0file36

## 4.2 best / base / worst を整理する

GenesisPrediction は単一未来を前提としない。

最低限

```text
best_case
base_case
worst_case
```

の3分岐を持つ。 この3分岐構造は Prediction Architecture の基本シナリオとして定義されている。 fileciteturn0file36

## 4.3 Drivers を明示する

各シナリオは

```text
drivers
```

を持つ。

これは

```text
なぜその未来が起こり得るのか
```

を説明するためである。

## 4.4 Watchpoints を明示する

各シナリオは

```text
watchpoints
```

を持つ。

これは

```text
どの観測が分岐更新の引き金になるか
```

を示す。

Prediction Layer では watchpoints が非常に重要な要素として位置づけられている。 fileciteturn0file35

## 4.5 Invalidation Conditions を明示する

各シナリオは

```text
invalidation_conditions
```

を持つ。

これは

```text
何が起きたらそのシナリオを捨てるべきか
```

を示す。

Scenario は可能性の整理であり、永続的真実ではない。

---

# 5. What Scenario Layer Must Not Do

Scenario Layer は次のことをしてはいけない。

## 5.1 観測を再生成しない

Scenario は observation / trend / signal を読むだけであり、
観測を作り直さない。

## 5.2 Prediction の最終文体を担わない

公開用 summary の最終整形は Prediction Layer の責務である。

## 5.3 UI の都合で分岐を捏造しない

UI は read-only であり、予測生成や probability の捏造は禁止されている。 Scenario Layer も UI に合わせて意味を歪めてはならない。 fileciteturn0file38turn0file40

## 5.4 単一未来へ圧縮しない

Scenario は分岐の層である。

```text
best/base/worst のうちどれか1つだけ残す
```

という設計は不可とする。

## 5.5 数学的に見せかけた疑似精度を出さない

確率や confidence は飾りではない。
Scenario Layer は精密そうな小数を乱発するよりも、
分岐の説明可能性を優先する。

---

# 6. Inputs

Scenario Layer は主に以下を入力とする。

```text
trend_latest.json
signal_latest.json
observation memory / history
optional: daily_summary_latest.json
optional: sentiment_latest.json
optional: health_latest.json
optional: fx inputs / overlay summary
```

ただし正式な直入力は

```text
signal_latest.json
```

を中心とする。 Prediction Architecture では Scenario Engine の入力は signal_latest.json と定義されている。 fileciteturn0file36

補足として Trend や Observation Memory を参照してよいが、
Scenario の生成根拠は必ず Signal と整合していなければならない。

---

# 7. Minimal Output

Scenario Layer の最低出力はこれとする。

```text
analysis/prediction/scenario_latest.json
```

Prediction Architecture では Scenario Engine の出力として `scenario_latest.json` が想定されている。 fileciteturn0file36

最低限含むべき要素

```text
as_of
horizon_days
scenario_count
dominant_path
best_case
base_case
worst_case
watchpoints
drivers
invalidation_conditions
confidence
scenario_probabilities
signal_summary
```

---

# 8. Standard Scenario Set

v1 の標準シナリオ集合は次の3つとする。

## 8.1 Best Case

意味

```text
緊張が緩和し、観測上の悪化シグナルが弱まる分岐
```

例

- risk 上昇が止まる
- negative persistence が鈍化する
- volatility expansion が収束する
- regime shift signal が不成立になる

## 8.2 Base Case

意味

```text
現行レジームが継続し、現状延長線上で推移する分岐
```

例

- mixed uncertainty が継続する
- risk は高止まりだが急拡大しない
- attention topic は継続するが破局化しない

## 8.3 Worst Case

意味

```text
悪化シグナルが連鎖し、緊張や混乱が拡大する分岐
```

例

- acceleration + anomaly が重なる
- regime_shift が確定方向へ進む
- volatility expansion が継続する
- negative / uncertainty cluster が強化される

---

# 9. Scenario Object Design

各シナリオは共通 object structure を持つ。

```text
id
label
direction
summary
probability
confidence
drivers[]
watchpoints[]
invalidation_conditions[]
expected_signals[]
implications[]
risk_level
```

意味

## id

内部識別子

例

```text
best_case
base_case
worst_case
```

## label

表示用名称

## direction

分岐方向

例

```text
easing
persistence
escalation
```

## summary

その分岐の短い説明

## probability

その分岐の相対的重み

## confidence

その分岐が current observation とどれだけ整合するか

## drivers

シナリオを支える要因

## watchpoints

分岐更新の監視点

## invalidation_conditions

崩れる条件

## expected_signals

そのシナリオが続くなら次に出やすい Signal

## implications

Human が受け取るべき意味

## risk_level

そのシナリオ下での危険度ラベル

---

# 10. Probability Rule

Scenario Layer は probability を持ってよい。

ただし意味は

```text
厳密な未来確率
```

ではなく

```text
現時点の観測と signal に照らした相対的妥当度
```

とする。

重要原則

```text
Probability is ranking, not prophecy
```

v1 の運用ルール

- 3シナリオ合計で 1.0 を目安に正規化してよい
- 小数第2位程度までで十分
- 根拠のない極端値は禁止
- dominant scenario は最高 probability のものとする
- ただし dominant でも single truth ではない

---

# 11. Confidence Rule

Scenario Layer における confidence は
Prediction Layer 全体の原則に従う。

confidence は

```text
当たる確率
```

ではなく

```text
観測・trend・signal・scenario の整合性の強さ
```

である。 fileciteturn0file35

Scenario Layer では confidence を次の材料から構成する。

- input data sufficiency
- trend clarity
- signal strength
- scenario separation clarity
- invalidation clarity

重要原則

```text
confidence を飾りにしない
```

---

# 12. Driver Rule

drivers は Scenario の心臓部である。

各シナリオは最低3つ前後の drivers を持つことを推奨する。

driver の性質

- 短い文で書く
- trend / signal と対応する
- 原因ではなく「現在その分岐を支持する観測理由」を書く
- 同じ driver を best/base/worst にコピペしない

良い例

```text
negative coverage remained elevated for 3 days
regime_shift signal emerged after persistent uncertainty rise
fx volatility expanded while sentiment clarity weakened
```

悪い例

```text
some risk exists
world is unstable
things may get worse
```

---

# 13. Watchpoint Rule

watchpoints は Scenario 運用の中核である。

Prediction Layer の設計原則では、watchpoints は

```text
未来を変える観測点
```

とされている。 fileciteturn0file35

Scenario Layer における watchpoints の役割

- 分岐更新条件を Human に明示する
- Early Warning を運用可能にする
- best/base/worst の移行条件を見える化する

watchpoint の書き方

- 観測可能なものにする
- 曖昧な精神論を書かない
- できれば次回 Morning Ritual で確認可能な形にする

例

```text
risk score rises again for 2 consecutive runs
new anomaly signal appears with higher confidence
worst_case probability overtakes base_case
negative cluster expands beyond current topic set
```

---

# 14. Invalidation Rule

各シナリオは最低1つ以上の invalidation condition を持つ。

理由

- シナリオを信仰対象にしないため
- 外れた時に学習できるようにするため
- Prediction を説明可能にするため

例

```text
acceleration signal disappears for 3 consecutive runs
headline intensity normalizes while uncertainty falls
expected regime shift does not persist into next window
```

重要原則

```text
Invalidation is part of intelligence
```

---

# 15. Early Warning Engine Relation

Scenario Layer は Early Warning Engine の中心に位置する。

役割

```text
Signal = 警報の種
Scenario = 警報の意味づけ
Prediction = 公開用の警報要約
```

Early Warning において重要なのは

```text
悪いことが起こると断言すること
```

ではなく

```text
どの悪化分岐が強まりつつあるかを早く示すこと
```

である。

したがって Scenario Layer は

- escalation path の可視化
- persistence path の監視
- easing path の残存可能性

を同時に扱う。

---

# 16. Horizon Rule

Prediction Architecture では horizon として

```text
3d
7d
30d
```

が定義され、v1 の標準は `7d` とされている。 fileciteturn0file36

Scenario Layer もこれに従う。

v1 ルール

```text
horizon_days = 7
```

将来拡張

- 3d では tactical early warning
- 7d では current scenario outlook
- 30d では structural scenario framing

ただし v1 では multi-horizon 同時生成は行わず、
まず 7d の一貫性を優先する。

---

# 17. Scenario Generation Logic (v1)

v1 の Scenario Engine は次の順で動く。

```text
1. signal_latest.json を読む
2. signal を type / strength / persistence で整理する
3. signal cluster を作る
4. cluster ごとに future direction を仮決定する
5. best / base / worst へ配分する
6. drivers / watchpoints / invalidation_conditions を生成する
7. probability / confidence を整形する
8. scenario_latest.json を出力する
```

ここで重要なのは

```text
signal cluster → scenario mapping
```

である。

単一シグナルから単純直結するのではなく、
複数シグナルの組み合わせを見る。

---

# 18. Signal-to-Scenario Mapping

v1 の基本マッピング指針

## 18.1 persistence

意味

```text
現行状態の継続
```

主に

```text
base_case
```

を強化する。

## 18.2 acceleration

意味

```text
現在の流れの増幅
```

悪化方向なら worst_case、
改善方向なら best_case を強化する。

## 18.3 reversal

意味

```text
現行流れの反転可能性
```

base_case を弱め、best または worst に資金移動させるような役割を持つ。

## 18.4 anomaly

意味

```text
通常パターンからの逸脱
```

worst_case の watchpoint または early escalation driver になりやすい。

## 18.5 regime_shift

意味

```text
構造変化の可能性
```

単なる短期変動ではなく、scenario dominance の更新要因になる。

## 18.6 volatility_expansion

意味

```text
不安定性の拡大
```

base-case persistence よりも branching width を広げる働きを持つ。

---

# 19. Standard JSON Shape (v1)

v1 の標準 shape は以下とする。

```json
{
  "as_of": "2026-03-09",
  "horizon_days": 7,
  "scenario_count": 3,
  "dominant_path": "base_case",
  "confidence": 0.68,
  "signal_summary": {
    "count": 4,
    "dominant_types": ["persistence", "acceleration"]
  },
  "scenario_probabilities": {
    "best_case": 0.22,
    "base_case": 0.51,
    "worst_case": 0.27
  },
  "best_case": {
    "id": "best_case",
    "label": "Easing path",
    "direction": "easing",
    "summary": "Current tension fades and negative momentum fails to persist.",
    "probability": 0.22,
    "confidence": 0.55,
    "risk_level": "guarded",
    "drivers": [],
    "watchpoints": [],
    "invalidation_conditions": [],
    "expected_signals": [],
    "implications": []
  },
  "base_case": {
    "id": "base_case",
    "label": "Persistent pressure",
    "direction": "persistence",
    "summary": "Current elevated uncertainty persists without decisive breakdown.",
    "probability": 0.51,
    "confidence": 0.68,
    "risk_level": "elevated",
    "drivers": [],
    "watchpoints": [],
    "invalidation_conditions": [],
    "expected_signals": [],
    "implications": []
  },
  "worst_case": {
    "id": "worst_case",
    "label": "Escalation path",
    "direction": "escalation",
    "summary": "Escalation signals chain together and instability broadens.",
    "probability": 0.27,
    "confidence": 0.61,
    "risk_level": "high",
    "drivers": [],
    "watchpoints": [],
    "invalidation_conditions": [],
    "expected_signals": [],
    "implications": []
  }
}
```

この shape は v1 の基準であり、将来拡張は許可する。
ただし best / base / worst の3本柱は維持する。

---

# 20. Storage Rule

保存場所は次を標準とする。

```text
analysis/prediction/scenario_latest.json
```

履歴保存は将来次を想定する。

```text
analysis/prediction/history/YYYY-MM-DD/scenario.json
```

Prediction Architecture では `analysis/prediction/` 配下に trend / signal / scenario / prediction を置く構造が定義されている。 fileciteturn0file36

---

# 21. Integration with Morning Ritual

Scenario Layer は Morning Ritual の Prediction lane に統合される。

理想的流れは Prediction Layer Principles でも示されている。 fileciteturn0file35

標準フロー

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
prediction history save
↓
UI update
```

重要原則

```text
Scenario は日次心拍で更新される仮説
```

---

# 22. Relation to Prediction Layer

Scenario Layer と Prediction Layer の違い

## Scenario Layer

- 分岐を作る
- 不確実性を保持する
- drivers / watchpoints / invalidation を整理する
- Human が今後を考えるための地図を作る

## Prediction Layer

- dominant scenario を要約する
- 公開用の summary を出す
- overall risk を短く示す
- Human がすぐ読める最終形に整える

重要原則

```text
Scenario が地図
Prediction が表紙
```

---

# 23. Failure Modes to Avoid

Scenario Layer で避けるべき失敗

## Failure 1

```text
Signal をそのまま文章化して終わる
```

## Failure 2

```text
best/base/worst の3分岐が実質同じ内容になる
```

## Failure 3

```text
watchpoints が抽象語だけになる
```

## Failure 4

```text
invalidation_conditions が無い
```

## Failure 5

```text
dominant scenario を真実扱いして他分岐を死文化する
```

## Failure 6

```text
UI都合でシナリオ内容を短絡化する
```

## Failure 7

```text
history を見ずに毎日その場で思いつき分岐を作る
```

---

# 24. Future Expansion

将来拡張候補

```text
multi-horizon scenarios
scenario tree
historical analog attachment
path dependency scoring
scenario drift tracking
cross-domain scenario link
FX-linked scenario overlays
```

ただし v1 では拡張よりも

```text
best/base/worst の説明可能性
```

を優先する。

---

# 25. Final Summary

GenesisPrediction の Scenario Layer は

```text
Signal から未来分岐を作る層
```

である。

構造

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

Scenario Layer の核心は

```text
best_case
base_case
worst_case
```

を通して

```text
不確実性を見える化し
危険分岐を早く整理し
Prediction を説明可能にすること
```

である。

最重要原則はこれである。

```text
Scenario は未来を断言しない
Scenario は未来分岐を整理する
```

これにより GenesisPrediction は

```text
単発予測システム
```

ではなく

```text
危険を早く知るための Explainable Branching System
```

として進化できる。

---

END OF DOCUMENT
