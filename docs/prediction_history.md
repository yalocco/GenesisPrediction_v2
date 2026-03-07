# Prediction History
GenesisPrediction v2

Status: Active
Purpose: Prediction Layer の履歴保存と時系列比較の設計
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```text
Prediction History Layer

を定義する。

目的

予測結果を日次で保存する

prediction_latest だけでなく prediction の推移を追えるようにする

scenario shift / risk drift / confidence drift を検出可能にする

将来の backtest / prediction review / drift analysis の土台を作る

Prediction UI を「今日だけ」から「時系列理解」へ進化させる

Prediction System は

prediction_latest.json

だけでは不十分である。

本当の価値は

予測がどう変化してきたか

にある。

1. Position in System

GenesisPrediction v2 の構造

data
↓
scripts
↓
analysis
↓
prediction
↓
UI

Prediction Layer 内部構造

Observation Memory
↓
Trend Engine
↓
Signal Engine
↓
Scenario Engine
↓
Prediction Engine
↓
Prediction History

Prediction History は

Prediction Engine の結果を保存し
時系列比較可能にする層

である。

2. Core Role

Prediction History Layer の役割

prediction_latest.json を日次保存する

scenario_latest.json も日次保存する

signal_latest.json も日次保存する

後日比較に必要な最小情報を蓄積する

「昨日より悪化したか」を判断できるようにする

つまり

Prediction の記憶層

である。

3. Storage Structure

正式保存先

analysis/prediction/history/YYYY-MM-DD/

例

analysis/prediction/history/2026-03-07/
  trend.json
  signal.json
  scenario.json
  prediction.json

analysis/prediction/history/2026-03-08/
  trend.json
  signal.json
  scenario.json
  prediction.json

重要原則

latest は最新表示用

history は時系列保存用

latest と history を混同しない

4. Minimum Saved Artifacts

Prediction History に最低限保存すべきもの

trend.json
signal.json
scenario.json
prediction.json

理由

trend.json

世界の流れの保存

signal.json

兆候検知の保存

scenario.json

未来分岐の保存

prediction.json

公開用予測の保存

この4つが揃うと

なぜその予測になったか

を後から追跡できる。

5. History Write Timing

Prediction History 保存タイミング

prediction_latest.json 生成成功後

順序

Trend latest 書き込み
↓
Signal latest 書き込み
↓
Scenario latest 書き込み
↓
Prediction latest 書き込み
↓
History snapshot 保存

重要原則

latest 成功が先
history 保存はその後

理由

最新成果物が主目的

history は追加価値

history 失敗で latest を壊さない

6. Date Rule

Prediction History の日付は

WorldDate

を使用する。

つまり Morning Ritual における prediction date と一致させる。

例

--date 2026-03-06

なら保存先は

analysis/prediction/history/2026-03-06/

とする。

これにより

Morning Ritual の date

analysis の dated artifact

prediction history

が一致する。

7. History Read Use Cases

Prediction History は以下に使う。

7.1 Scenario Shift

例

2026-03-06: base_case dominant
2026-03-07: worst_case dominant

これは

scenario shift

である。

7.2 Risk Drift

例

guarded
↓
elevated
↓
high

これは

risk deterioration

である。

7.3 Confidence Drift

例

0.78
↓
0.63
↓
0.49

confidence 低下は

不確実性増大

を意味する。

7.4 Watchpoint Persistence

同じ watchpoint が数日連続するなら

重要な継続兆候

と見なせる。

8. Derived History Metrics

Prediction History から将来算出する指標

dominant_scenario_streak
overall_risk_change
confidence_change
worst_case_probability_change
watchpoint_persistence
driver_persistence

これらは v1 では保存不要だが、
後で history から計算可能にする。

9. Prediction Review Concept

Prediction History があると

Prediction Review

が可能になる。

例

3日前は guarded
2日前は elevated
今日は critical

この変化を見ることで

AI の判断変化

世界状態の悪化

シグナルの蓄積

をレビューできる。

これは GenesisPrediction における

AIの思考ログ

に近い役割を持つ。

10. Backtest Bridge

Prediction History は将来の

backtest

にも接続する。

基本構造

過去の prediction
↓
実際に起きた結果
↓
一致 / 不一致

たとえば

worst_case probability が高かった日に実際に悪化したか

guarded 判定の日に安定したか

などを確認できる。

Prediction History は

予測精度検証

の前提条件である。

11. Comparison Target Fields

Prediction History 比較で重要な field

overall_risk
confidence
dominant_scenario
scenario_probabilities
summary
watchpoints
drivers
invalidation_conditions

特に重要なのは

overall_risk

危険度の推移

dominant_scenario

中心分岐の変化

scenario_probabilities

未来分岐バランスの変化

watchpoints

何を警戒していたか

drivers

何がその予測を支えたか

12. Optional Summary Index

将来的に history index を持ってもよい。

例

analysis/prediction/prediction_history_index.json

内容例

[
  {
    "date": "2026-03-06",
    "overall_risk": "elevated",
    "dominant_scenario": "base_case",
    "confidence": 0.69
  },
  {
    "date": "2026-03-07",
    "overall_risk": "critical",
    "dominant_scenario": "worst_case",
    "confidence": 0.81
  }
]

利点

UI が軽く履歴を読める

全日付の summary を一括で見られる

trend chart が作りやすい

ただし v1 では必須ではない。

13. Prediction History UI Possibility

将来の Prediction UI では
history を読むことで以下を追加できる。

risk trend chart

dominant scenario timeline

confidence timeline

scenario probability drift

watchpoint persistence list

これにより Prediction UI は

今日の予測表示

から

予測の流れを理解する画面

へ進化する。

14. History Integrity Rules

Prediction History の保存ルール

Rule 1
history は append-only

原則、過去日付ファイルを上書きしない。

Rule 2
latest と history を一致させる

history 保存時点の latest がその日の snapshot になる。

Rule 3
history 不整合で latest を壊さない
Rule 4
date folder を唯一の単位とする

1日 = 1 prediction snapshot セット

15. Runtime Integration

Prediction Runtime との関係

scripts/run_prediction_pipeline.py

はすでに

--write-history

で history 保存を行える。

つまり v1 では

Prediction History Layer = Runtime 連携済み

である。

次に必要なのは

設計の固定化

参照方法の固定化

UI/Review への接続

である。

16. Morning Ritual Meaning

Morning Ritual に history が入る意味

毎朝 prediction の記憶が1日分増える

ことである。

これは単なる latest 更新ではなく、

予測の蓄積

を意味する。

よって Morning Ritual は

世界観測の心拍

であるだけでなく、

未来予測記憶の心拍

にもなる。

17. Future Extensions

将来追加予定

prediction_history_index.json
prediction_drift_latest.json
scenario_shift_latest.json
prediction_review_latest.json
backtest_report.json

これにより

GenesisPrediction は

予測するAI

から

予測を振り返り学習するAI

へ進化する。

18. Design Principles

Prediction History の原則

Principle 1

History は

prediction_latest のコピー保管

ではなく、

時系列理解の土台

である。

Principle 2

History は

予測の変化

を見るために存在する。

Principle 3

History は

説明可能性

を高める。

Principle 4

History は

将来の backtest

に接続する。

Principle 5

History は

Prediction Memory

である。

19. Final Role

Prediction History Layer は

GenesisPrediction の予測記憶

である。

今日の予測だけではなく、

昨日どう見ていたか
一昨日どう見ていたか
何が変わったか

を残すことで、

GenesisPrediction は本当の意味で

未来を見続けるAI

へ進化する。

END OF DOCUMENT