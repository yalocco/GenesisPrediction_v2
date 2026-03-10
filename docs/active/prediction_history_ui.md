# Prediction History UI
GenesisPrediction v2

Status: Active
Purpose: Prediction History を可視化する UI 設計
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```text
Prediction History UI

を定義する。

目的

prediction の推移を人間が見えるようにする

overall_risk の変化を可視化する

dominant_scenario の切り替わりを見えるようにする

confidence の drift を見えるようにする

worst_case probability の推移を確認できるようにする

Prediction System を「今日の表示」から「時系列理解」へ進化させる

Prediction UI v1 は

今日の予測

を表示する。

Prediction History UI は

予測の流れ

を表示する。

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

Prediction Layer 内部

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
↓
Prediction History UI

Prediction History UI は

Prediction Memory を人間が読む画面

である。

2. Core Role

Prediction History UI の役割

日次 prediction を並べる

risk の悪化 / 改善を把握する

scenario shift を把握する

confidence の揺れを把握する

予測が安定しているか / 不安定かを見る

将来の backtest / review への入口になる

つまり

予測の履歴ダッシュボード

である。

3. Primary Data Sources

Prediction History UI が読む正式データ

Current latest
analysis/prediction/prediction_latest.json
History snapshots
analysis/prediction/history/YYYY-MM-DD/prediction.json

将来の軽量 index 候補

analysis/prediction/prediction_history_index.json

v1 では index が無くても成立するが、
将来的には index を優先参照する。

4. UI Goals

Prediction History UI の目標

Goal 1
risk の流れを一目で見る
Goal 2
dominant_scenario の変化を見る
Goal 3
confidence が下がっていないか見る
Goal 4
worst_case が積み上がっていないか見る
Goal 5
AIの予測がどの方向へ動いているか見る
5. Main Views

Prediction History UI は最低限、以下の view を持つ。

5.1 Risk Timeline

表示内容

date
overall_risk

例

2026-03-04 guarded
2026-03-05 elevated
2026-03-06 high
2026-03-07 critical

意味

危険度の推移

これは最も重要な履歴表示である。

5.2 Dominant Scenario Timeline

表示内容

date
dominant_scenario

例

2026-03-04 best_case
2026-03-05 base_case
2026-03-06 base_case
2026-03-07 worst_case

意味

未来分岐の中心がどう変わったか

これは

scenario shift

を見るための表示である。

5.3 Confidence Timeline

表示内容

date
confidence

例

0.82
0.76
0.68
0.51

意味

予測の確信度が下がっているか

confidence 低下は

不確実性増加

として重要である。

5.4 Scenario Probability Trend

表示内容

best_case
base_case
worst_case

各 probability の推移。

例

worst_case: 0.12 → 0.18 → 0.31 → 0.63

意味

悪化分岐が積み上がっているか

これは Prediction History UI の中心チャート候補である。

5.5 Watchpoint Persistence

表示内容

watchpoints が何日連続で出ているか

例

headline_risk_pressure 4 days
volatility_breakout 2 days
uncertainty 5 days

意味

継続警戒対象

である。

6. Recommended UI Sections

Prediction History UI は以下のセクションを持つのが望ましい。

Section A: Current vs Yesterday

表示

today
yesterday
delta

対象

overall_risk

confidence

dominant_scenario

worst_case probability

例

overall_risk: high → critical
confidence: 0.68 → 0.81
dominant: base_case → worst_case
worst_case: 0.25 → 0.63

これにより

今日何が変わったか

がすぐ分かる。

Section B: 7-day Timeline

表示

過去7日

対象

risk

dominant scenario

confidence

これは最小構成として最重要。

Section C: Scenario Drift

表示

best/base/worst の確率推移

意味

未来分岐の重心移動
Section D: Persistent Watchpoints

表示

継続して出ている watchpoint

例

headline risk
fx volatility
uncertainty
Section E: Prediction Review Notes

将来用の枠。

内容

前日との差分要約

例

Worst-case probability rose sharply as headline pressure and uncertainty persisted.

v1 では手動または簡易自動でもよい。

7. Visual Design Principles

Prediction History UI の見た目原則

Principle 1
今日より流れを優先

v1 Prediction UI は「今日の予測」中心。
History UI は「変化」中心。

Principle 2
色は risk semantics に連動

例

low = green

guarded = yellow

elevated = orange

high = red

critical = magenta

Principle 3
折れ線 / ステップ表示を使う

confidence や probability は line chart 向き。
risk label は step/timeline 向き。

Principle 4
1画面で理解できる

複雑すぎる drilldown より、
まず 7日〜30日の変化を一目で見せる。

8. Risk Timeline Mapping

overall_risk は文字列だが、
UI 表示や簡易 chart のために内部マッピングを持ってよい。

例

low      = 1
guarded  = 2
elevated = 3
high     = 4
critical = 5

重要原則

これは表示用マッピングであり
risk 自体の真実は文字列

である。

9. Dominant Scenario Mapping

dominant_scenario の表示候補

best_case
base_case
worst_case

UI では

Best
Base
Worst

の pill / timeline 表示が適切。

将来 scenario 種類が増えても、
最初はこの3分類を基準にする。

10. Prediction Delta Concept

Prediction History UI では

prediction delta

を表示すると強い。

対象例

overall_risk delta

confidence delta

worst_case probability delta

dominant scenario changed or not

new watchpoints / disappeared watchpoints

例

worst_case +31pt
confidence +0.13
dominant changed: base → worst

これは

今日の変化を一瞬で理解する欄

として有効。

11. History Window Strategy

UI の標準 window

7d
短期レビュー
30d
構造変化レビュー

v1 では

7d default

が最も良い。

理由

読みやすい

日次予測と相性が良い

Morning Ritual の rhythm に合う

12. Fallback Strategy

Prediction History UI の fallback

Priority 1
prediction_history_index.json

あれば最優先。

Priority 2
history/YYYY-MM-DD/prediction.json

を列挙して読む。

Priority 3

history が無い場合は

prediction_latest.json のみ表示

にフォールバックする。

重要原則

履歴が無くてもUIが落ちない
13. Interaction Design

将来の操作候補

7d / 30d 切替

risk only / confidence only / scenario only の表示切替

latest へ戻る

raw JSON を開く

history date をクリックしてその日の prediction.json を開く

ただし v1 では

表示を簡潔に保つ

ことを優先する。

14. Derived Insight Blocks

History UI にあると強い派生表示

14.1 Risk Streak

例

critical streak: 3 days
14.2 Worst-case Expansion

例

worst_case rising for 4 days
14.3 Scenario Stability

例

dominant scenario unchanged for 5 days
14.4 Confidence Instability

例

confidence volatility high

これらは v2 以降で追加しやすい。

15. Relation to Prediction Review

Prediction History UI は将来の

Prediction Review

の入口になる。

Review の役割

予測がどう変わったか振り返る

現実と比べる

AIの判断の癖を見る

History UI はその土台として

まず変化を見せる

ことが役割である。

16. Future Data Contract

将来的に UI 最適化のため、
次のような index を持つことが望ましい。

[
  {
    "date": "2026-03-06",
    "overall_risk": "elevated",
    "confidence": 0.69,
    "dominant_scenario": "base_case",
    "best_case": 0.18,
    "base_case": 0.57,
    "worst_case": 0.25
  },
  {
    "date": "2026-03-07",
    "overall_risk": "critical",
    "confidence": 0.81,
    "dominant_scenario": "worst_case",
    "best_case": 0.05,
    "base_case": 0.32,
    "worst_case": 0.63
  }
]

これにより UI は軽く、単純になる。

17. Suggested File Structure

将来の UI ファイル候補

app/static/prediction_history.html

必要に応じて

app/static/common/prediction_history.js

へ分離してもよい。

ただし v1 は

単一HTMLでも可

とする。

18. Design Principles

Prediction History UI の原則

Principle 1
history は「蓄積」ではなく「変化理解」のため
Principle 2
今日より、昨日からどう動いたかを重視する
Principle 3
Prediction UI と役割を分ける

prediction.html = 今日の予測

prediction_history.html = 予測の流れ

Principle 4
表示は read-only

ロジックは scripts / prediction outputs に置く。

Principle 5
将来の review / backtest に接続しやすくする
19. Final Role

Prediction History UI は

GenesisPrediction の予測の流れを見せる窓

である。

今日の予測だけではなく、

悪化しているのか
改善しているのか
最悪分岐が積み上がっているのか
AIが自信を失っているのか

を見せることで、

GenesisPrediction は本当の意味で

未来を追跡するAI

へ進化する。

END OF DOCUMENT