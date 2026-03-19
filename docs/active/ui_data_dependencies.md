# UI Data Dependencies

GenesisPrediction v2

Version: 1.6
Status: Active
Purpose: UI がどのデータを読むか、どの field に依存するか、fallback をどう扱うか、さらに UI 用語の意味をどう固定するか、および Explanation Layer をどう参照するかを定義する
Last Updated: 2026-03-19

---

# Overview

このドキュメントは、GenesisPrediction v2 の UI とデータ依存関係を記録する。

目的:

- AI が毎回データ構造を探し直すことを防ぐ
- UI 改修時の事故を防ぐ
- fallback 挙動を明文化する
- scripts / analysis / UI の責務を分離して保つ
- 統一済み UI レイアウトとデータ依存を対応づける
- UI に表示される主要用語の意味を固定する
- Tooltip / detail / explanation layer の意味基盤を用意する
- Explanation Layer の UI 参照ルールを固定する

重要原則:

```text
scripts → analysis を生成
analysis → Runtime SST
UI → analysis を読む
UI は再計算しない
UI は意味を再定義しない
UI は explanation を作文しない
````

つまり

```text
analysis = Single Source of Truth
```

UI 側でロジックを持つ場合も、それは表示や fallback のみであり、
分析値そのものの決定は scripts / analysis 側で行う。

また、UI に表示される言葉の意味は、
場当たり的に各ページへ分散定義してはならない。
意味定義は本ドキュメント内の UI Meaning Layer に集約する。

Explanation Layer も同様に、
UI が自由作文するのではなく、
analysis 側の explanation artifact を読む構造を正とする。

---

# Index

## 1. Runtime / Page Dependencies

* [Overview](#overview)
* [Runtime Layout](#runtime-layout)
* [Explanation Layer Runtime Layout](#explanation-layer-runtime-layout)
* [Home Page](#home-page)
* [Overlay Page](#overlay-page)
* [Sentiment Page](#sentiment-page)
* [Digest Page](#digest-page)
* [Prediction Page](#prediction-page)
* [Prediction History Page](#prediction-history-page)
* [UI Data Flow](#ui-data-flow)
* [Explanation Data Flow](#explanation-data-flow)
* [Fallback Rules](#fallback-rules)
* [Explanation Fallback Rules](#explanation-fallback-rules)
* [Design Rules](#design-rules)

## 2. UI Meaning Layer

* [UI Meaning Layer](#ui-meaning-layer)
* [Meaning Layer Rules](#meaning-layer-rules)
* [Meaning Dictionary](#meaning-dictionary)

### Core Time / Status Terms

* [as_of](#as_of)
* [updated](#updated)
* [global_risk](#global_risk)
* [health](#health)
* [unknown](#unknown)
* [unavailable](#unavailable)
* [loading](#loading)
* [fallback](#fallback)

### Sentiment / Digest Terms

* [sentiment](#sentiment)
* [positive](#positive)
* [negative](#negative)
* [neutral](#neutral)
* [mixed](#mixed)
* [summary](#summary)
* [highlight](#highlight)
* [article](#article)

### Overlay / FX Terms

* [fx_signal](#fx_signal)
* [decision](#decision)
* [reason](#reason)
* [fx_explanation](#fx_explanation)

### Prediction / History Terms

* [scenario](#scenario)
* [dominant_scenario](#dominant_scenario)
* [best_case](#best_case)
* [base_case](#base_case)
* [worst_case](#worst_case)
* [confidence](#confidence)
* [drivers](#drivers)
* [watchpoints](#watchpoints)
* [invalidation](#invalidation)
* [implications](#implications)
* [drift](#drift)
* [risk drift](#risk-drift)
* [confidence drift](#confidence-drift)
* [scenario shift](#scenario-shift)
* [explanation](#explanation)
* [headline](#headline)
* [why_it_matters](#why_it_matters)
* [must_not_mean](#must_not_mean)
* [ui_terms](#ui_terms)

## 3. Maintenance / Operations

* [Meaning Layer Integration Guidance](#meaning-layer-integration-guidance)
* [Explanation Layer Integration Guidance](#explanation-layer-integration-guidance)
* [Relation to Layout Standard](#relation-to-layout-standard)
* [When Updating UI](#when-updating-ui)
* [Troubleshooting Hints](#troubleshooting-hints)
* [Future Expansion](#future-expansion)

## 4. Quick Usage Guide

* UI source を確認したいときは **Page Dependencies** を見る
* explanation source を確認したいときは **Explanation Layer Runtime Layout** を見る
* fallback 順序を確認したいときは **Fallback Rules** を見る
* explanation fallback を確認したいときは **Explanation Fallback Rules** を見る
* 用語の意味を確認したいときは **Meaning Dictionary** を見る
* UI変更時の確認順は **When Updating UI** を見る

---

# Runtime Layout

主要な UI ファイル:

```text
app/static/index.html
app/static/overlay.html
app/static/sentiment.html
app/static/digest.html
app/static/prediction.html
app/static/prediction_history.html
```

共通 UI 部品:

```text
app/static/app.css
app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js
```

主要なデータ配置:

```text
data/world_politics/analysis/
data/digest/
data/fx/
analysis/prediction/
analysis/prediction/history/
analysis/explanation/
```

補足:

* 全主要ページは共通 header / footer / layout.js を使う
* レイアウト標準は `docs/ui_layout_standard.md` に従う
* UI は data / analysis の latest または history を読む read-only レイヤである

---

# Explanation Layer Runtime Layout

Explanation Layer の正式配置は以下を想定する。

```text
analysis/explanation/

prediction_explanation_latest.json
scenario_explanation_latest.json
signal_explanation_latest.json
fx_explanation_latest.json
world_explanation_latest.json
```

重要原則:

* explanation は UI 内で自由作文しない
* explanation は analysis 側 artifact として生成する
* UI は explanation artifact を読み、表示するだけ
* explanation は prediction / scenario / signal / fx / world の既存判断結果を人間可読構造へ変換したもの
* explanation は新しい真実を作らない

想定される共通 explanation schema:

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

UI が explanation から表示してよい代表 field:

```text
headline
summary
why_it_matters
drivers[]
watchpoints[]
invalidation[]
must_not_mean[]
ui_terms[]
```

UI が explanation からやってはいけないこと:

```text
不足 field を勝手に推論する
confidence の意味を再定義する
prediction から explanation を再生成する
explanation artifact が無いのに explanation ありのふりをする
```

---

# Home Page

File:

```text
app/static/index.html
```

## Primary Purpose

Home はプロジェクトの入口ページであり、
各ページへの導線と latest 状態の確認を行う。

## Main Dependencies

主に以下の latest 系を参照する想定:

```text
data/digest/view_model_latest.json
data/world_politics/analysis/daily_summary_latest.json
data/digest/health_latest.json
data/world_politics/analysis/sentiment_latest.json
analysis/explanation/world_explanation_latest.json
```

## Notes

* Home は集約表示ページ
* Summary は `daily_summary_latest.json` を優先参照する
* World explanation を表示する場合は `analysis/explanation/world_explanation_latest.json` を正式 source とする
* Events(today) は `data/digest/view_model_latest.json` の highlights / cards を使う
* Data Health は `health_latest.json.summary.ok / warn / ng / total` を使う
* Sentiment snapshot は Sentiment ページと揃えるため `data/world_politics/analysis/sentiment_latest.json` を優先参照する
* 詳細分析は Sentiment / Digest / Overlay / Prediction 側で行う
* latest alias の鮮度が重要

---

# Overlay Page

File:

```text
app/static/overlay.html
```

## Primary Purpose

FX / overlay の判断結果を表示する。

## Current Runtime Model

Overlay は pair selector に応じて
**pair ごとの image candidates / decision JSON candidates** を順に探索し、
最初に取得できたものを表示する。

UI はこの fallback を使って表示を継続するが、
これは表示継続のための read-only fallback であり、
正式なデータ生成責務は scripts / FX lane 側にある。

## Image Sources

### JPYTHB

画像は以下の順で探索する。

```text
/data/fx/fx_overlay_latest_jpythb.png
/data/fx/jpy_thb_remittance_overlay.png
/data/fx/fx_jpy_thb_overlay.png
```

### USDJPY

画像は以下の順で探索する。

```text
/data/fx/fx_overlay_latest_usdjpy.png
/data/fx/fx_jpy_usd_overlay.png
```

### USDTHB

画像は以下の順で探索する。

```text
/data/fx/fx_overlay_latest_usdthb.png
/data/fx/fx_multi_usd_thb_overlay.png
```

補足:

* 現在の repo では `fx_overlay_latest_usdthb.png` が存在しない場合がある
* その場合 Overlay UI は `fx_multi_usd_thb_overlay.png` を fallback として使う

### MULTI

画像は以下の順で探索する。

```text
/data/fx/fx_overlay_multi_latest.png
/data/fx/fx_multi_overlay.png
```

## Decision JSON Sources

Overlay decision JSON は以下の順で探索する。

### JPYTHB

```text
/data/fx/fx_decision_latest_jpythb.json
/data/fx/fx_decision_latest.json
```

### USDJPY

```text
/data/fx/fx_decision_latest_usdjpy.json
/data/fx/fx_decision_latest.json
```

### USDTHB

```text
/data/fx/fx_decision_latest_usdthb.json
/data/fx/fx_decision_latest.json
```

補足:

* 現在の repo では `fx_decision_latest_usdthb.json` が存在しない場合がある
* その場合 Overlay UI は `fx_decision_latest.json` を fallback として使う

### MULTI

```text
/data/fx/fx_decision_latest_multi.json
/data/fx/fx_decision_latest.json
```

## Explanation Source

FX explanation を表示する場合の正式 source:

```text
analysis/explanation/fx_explanation_latest.json
```

説明欄を持つ場合、FX decision JSON の `reason` は短い根拠、
`fx_explanation_latest.json` は構造化説明として扱う。

## Decision Field Handling

Overlay UI が decision JSON から参照する代表 field:

```text
decision
action
status
recommendation
reason
rationale
message
note
```

取得優先順:

### decision value

```text
decision
action
status
recommendation
```

### reason value

```text
reason
rationale
message
note
```

## Overlay Explanation Fields

Overlay explanation で表示してよい代表 field:

```text
headline
summary
why_it_matters
drivers[]
watchpoints[]
must_not_mean[]
```

## Overlay UI Fields

現在の Overlay UI は表示用に以下を保持する。

```text
pair
decision
reason
image
image_state
json_state
source
pair_note
```

Overlay explanation を追加する場合は以下も保持してよい:

```text
explanation_state
explanation_source
```

## Notes

* Overlay は FX 判断系の表示ページ
* 主 source は `data/fx/`
* UI は fallback を行うが、正式な latest 命名・pair 別成果物の整備は scripts 側責務
* `USDTHB` は現状 fallback 表示で動作するが、将来的には pair-specific latest の生成が望ましい
* 説明構造が必要な場合は `analysis/explanation/fx_explanation_latest.json` を読む
* 詳細仕様は docs/ui_system.md と docs/pipeline_system.md に従う

---

# Sentiment Page

File:

```text
app/static/sentiment.html
```

## Primary Data Source

```text
data/world_politics/analysis/sentiment_latest.json
```

## Fallback Source

原則 fallback しない。
どうしても必要な場合のみ以下を補助参照:

```text
data/world_politics/analysis/sentiment_timeseries.csv
data/world_politics/analysis/daily_news_latest.json
```

## Root Structure

想定構造:

```text
date
generated_at
items[]
today
summary
base
base_date
```

## Item Fields

記事単位の sentiment item は少なくとも以下を持つ:

```text
url
title
source
description
risk
positive
uncertainty
net
score
sentiment
sentiment_label
method
```

## KPI Source

Sentiment page の KPI は、原則として article item 群または today / summary を元に構築する。

重要分類 field:

```text
positive
negative
neutral
mixed
unknown
```

実際の label 取得は以下優先順で扱う:

```text
sentiment_label
sentiment
label
```

## Thumbnail

Primary source:

```text
urlToImage
image
thumbnail
```

Fallback:

```text
favicon
placeholder
非表示
```

## Trend / Time Series

Sentiment trend 表示は主に以下を読む:

```text
data/world_politics/analysis/sentiment_timeseries.csv
```

## Notes

* Sentiment page は per-article sentiment 表示が主目的
* score / net / risk / positive / uncertainty の表示は UI 側で再計算しない
* label の判定は scripts/build_daily_sentiment.py 側を正とする

---

# Digest Page

File:

```text
app/static/digest.html
```

## Primary Data Source

Digest の正式な source of truth はこれ:

```text
data/digest/view_model_latest.json
```

これは Digest UI の正式依存先であり、
KPI / cards / thumbnail / sentiment label は原則ここから構築する。

## Allowed Fallback Sources

Digest JSON が取得不能、または想定構造を満たさない場合のみ以下へ fallback してよい:

```text
data/world_politics/analysis/daily_summary_latest.json
data/world_politics/analysis/daily_news_latest.json
```

ただし fallback は暫定表示用であり、
正式運用では `data/digest/view_model_latest.json` を使うこと。

## Root Structure

Digest ViewModel の主要構造:

```text
version
date
sections[]
meta
sentiment_summary
today
```

## Section Structure

Digest の Top highlights は以下を読む:

```text
sections[].cards[]
```

通常は `world_politics` section を対象とする。

## Card Fields

Digest card は最低限以下を持つ想定:

```text
title
summary
source
url
image
tags
sentiment
```

sentiment object の代表 field:

```text
risk
positive
uncertainty
net
score
sentiment
sentiment_label
```

## KPI Source

Digest KPI は、原則としてこれを最優先で読む:

```text
sentiment_summary
```

Digest UI は `cards[]` から件数を再集計してもよいが、
正式な全体件数と分類件数は `sentiment_summary` を正とする。

### Required KPI Fields

```text
articles
positive_count
negative_count
neutral_count
mixed_count
unknown_count
net
score
risk
positive
uncertainty
riskScore
posScore
uncScore
```

## today Structure

Digest ViewModel では次も保持してよい:

```text
today.sentiment
today.sentiment_summary
```

Digest UI は以下優先順で KPI summary を取得してよい:

```text
sentiment_summary
today.sentiment_summary
today.sentiment
```

## Summary Text

Digest の Summary セクションに表示する summary text は、
Digest ViewModel 側に summary がある場合それを優先する。

Digest ViewModel に summary text が無い場合は、以下を暫定利用してよい:

```text
daily_summary_latest.json の summary / text_summary / daily_summary / yesterday_summary_text
```

## Digest Item Count

Digest UI の上部メタ表示 `items` は、
通常は `sections[world_politics].cards.length` を表示する。

注意:

```text
items != sentiment_summary.articles
```

となる場合がある。

理由:

* `cards[]` は Top highlights 用の抽出結果
* `sentiment_summary.articles` は全 article 件数

この違いは仕様であり、異常ではない。

## Thumbnail

Digest card のサムネイル source は以下優先順で扱う:

```text
image
urlToImage
thumbnail
```

Digest ViewModel では `image` に正規化して入れるのが望ましい。

Fallback:

```text
favicon
first-letter placeholder
no-image placeholder
```

## Sorting

Digest UI の代表 sort:

```text
risk
score
newest
```

重要原則:

* risk / score は card.sentiment 側の値を利用
* UI は再計算しない
* 並び替えは表示順の変更のみ

## Sentiment Label Handling

Digest card の label は以下優先順で読む:

```text
card.sentiment.sentiment_label
card.sentiment.sentiment
card.sentiment.label
```

card 直下に同名 field が存在する旧 schema にも、可能な限り後方互換対応してよい。

## Notes

* Digest の正式 source は `view_model_latest.json`
* `daily_news_latest.json` は fallback 用
* `unknown` が大量発生する場合は、まず `view_model_latest.json` の `cards[].sentiment` を確認する
* KPI が cards 件数と一致しない場合、`sentiment_summary` を見て仕様通りか判断する
* 現行 UI では Highlights は KPI 表示専用であり、記事カードは Articles セクションへ集約する

---

# Prediction Page

File:

```text
app/static/prediction.html
```

## Primary Data Source

Prediction の正式な source of truth はこれ:

```text
analysis/prediction/prediction_latest.json
```

Prediction UI は Runtime が出力した latest prediction snapshot を表示する。

## Explanation Source

Prediction explanation の正式 source はこれ:

```text
analysis/explanation/prediction_explanation_latest.json
```

Scenario explanation を併用する場合の正式 source:

```text
analysis/explanation/scenario_explanation_latest.json
```

Signal explanation を補助表示する場合の正式 source:

```text
analysis/explanation/signal_explanation_latest.json
```

## Allowed Supporting Sources

Prediction page は上部 Global Status の共通表示のため、補助的に以下を読んでよい:

```text
data/digest/view_model_latest.json
data/world_politics/analysis/daily_summary_latest.json
data/world_politics/analysis/sentiment_latest.json
data/fx/fx_decision_latest.json
```

ただし、Prediction の本体内容は `analysis/prediction/prediction_latest.json` を正とする。

## Expected Root Structure

Prediction JSON は少なくとも以下のような情報を含む想定:

```text
as_of
horizon_days
overall_risk
dominant_scenario
summary
confidence
scenarios
watchpoints
drivers
invalidation
implications
signal_count
```

補足:

* 実 runtime schema は進化してよい
* UI は後方互換的に複数 field 名を拾ってよい
* ただし UI が確率や risk を独自再計算してはならない

## Scenario Probabilities

Prediction UI が主に参照するのは以下:

```text
best_case
base_case
worst_case
```

または

```text
scenarios.best
scenarios.base
scenarios.worst
```

または scenario list 内の確率 field。

UI は schema 差分を吸収してよいが、
値の意味づけそのものは runtime 側を正とする。

## Core Display Fields

Prediction UI で主要表示する代表項目:

```text
overall_risk
dominant_scenario
summary
confidence
as_of
horizon_days
signal_count
```

## Section Fields

Prediction 下段詳細では以下のような配列 / テキストを参照する想定:

```text
watchpoints[]
drivers[]
invalidation[]
implications[]
```

UI は表示のために配列を整形してよいが、
重要度判定や抽出ロジックを再実装してはならない。

## Explanation Fields

Prediction explanation で表示してよい代表項目:

```text
headline
summary
why_it_matters
based_on[]
drivers[]
watchpoints[]
invalidation[]
must_not_mean[]
ui_terms[]
```

Scenario explanation で表示してよい代表項目:

```text
headline
summary
why_it_matters
drivers[]
watchpoints[]
invalidation[]
must_not_mean[]
```

Signal explanation で表示してよい代表項目:

```text
headline
summary
why_it_matters
based_on[]
drivers[]
watchpoints[]
must_not_mean[]
```

## Notes

* Prediction は runtime output の可視化ページ
* 正式 source は `analysis/prediction/prediction_latest.json`
* explanation を表示する場合の正式 source は `analysis/explanation/*.json`
* Global Status は共通UI用の補助表示であり、Prediction判定そのものではない
* ボタンで JSON を開く場合も、prediction latest を最優先とする
* UI は prediction から explanation を再生成してはならない

---

# Prediction History Page

File:

```text
app/static/prediction_history.html
```

## Primary Data Source

Prediction History の正式な source of truth はこれ:

```text
analysis/prediction/history/YYYY-MM-DD/prediction.json
```

Prediction History UI は history 配下の時系列 prediction snapshot 群を読み、
ドリフト / リスク変化 / confidence 変化を表示する。

## Optional Explanation Sources

Prediction History は Phase1 では explanation history を必須としない。

将来的に explanation history を追加する場合の想定配置:

```text
analysis/prediction/history/YYYY-MM-DD/prediction_explanation.json
analysis/prediction/history/YYYY-MM-DD/scenario_explanation.json
analysis/prediction/history/YYYY-MM-DD/signal_explanation.json
```

Phase1 では latest explanation を history の代用にしない。

## Supporting Sources

上部 Global Status の共通表示のため、補助的に以下を読んでよい:

```text
data/digest/view_model_latest.json
data/world_politics/analysis/daily_summary_latest.json
data/world_politics/analysis/sentiment_latest.json
data/fx/fx_decision_latest.json
```

ただし、History の本体表示は history prediction 群を正とする。

## History Scan Model

Prediction History UI は以下のような探索を行ってよい:

```text
analysis/prediction/history/*/prediction.json
```

または window 制御付きで:

```text
latest 7
latest 30
all available
```

これは表示対象の抽出であり、
履歴データ自体の再計算ではない。

## Expected Fields

各 history prediction snapshot では少なくとも以下を扱えるのが望ましい:

```text
as_of
overall_risk
dominant_scenario
confidence
best_case
base_case
worst_case
watchpoints
```

## Derived Presentation

Prediction History UI は複数 snapshot を比較して、
以下のような表示用差分を出してよい:

```text
risk drift
confidence drift
worst-case drift
scenario shift
persistent watchpoints
```

重要原則:

* これは表示比較であり、分析再計算ではない
* 元 snapshot の値を加工しすぎない
* 過去値 → 現在値の比較表示に留める

## Notes

* Prediction History は時系列 review ページ
* 上部 Global Status は他ページと同型の 5-card 横並びを標準とする
* 本体は history snapshot の比較表示に集中する
* latest と history の schema 差がある場合、UI は後方互換吸収をしてよい
* explanation history が無い場合、latest explanation を history 本文へ流用しない

---

# UI Data Flow

Digest の正式データフロー:

```text
daily_news_latest.json
↓
build_daily_sentiment.py
↓
sentiment_latest.json
↓
build_digest_view_model.py
↓
data/digest/view_model_latest.json
↓
app/static/digest.html
```

Sentiment の正式データフロー:

```text
daily_news_latest.json
↓
build_daily_sentiment.py
↓
sentiment_latest.json
↓
app/static/sentiment.html
```

Overlay の現行表示フロー:

```text
data/fx/*overlay*.png
+
data/fx/fx_decision_latest_<pair>.json
↓
fallback
↓
data/fx/fx_decision_latest.json
↓
app/static/overlay.html
```

Prediction の正式データフロー:

```text
signals / scenarios / runtime inputs
↓
prediction runtime
↓
analysis/prediction/prediction_latest.json
↓
app/static/prediction.html
```

Prediction History の正式データフロー:

```text
prediction runtime
↓
analysis/prediction/history/YYYY-MM-DD/prediction.json
↓
window scan / latest-first selection
↓
app/static/prediction_history.html
```

---

# Explanation Data Flow

Prediction explanation の正式データフロー:

```text
analysis/prediction/prediction_latest.json
+
analysis/prediction/scenario_latest.json
+
analysis/prediction/signal_latest.json
↓
explanation build
↓
analysis/explanation/prediction_explanation_latest.json
↓
app/static/prediction.html
```

Scenario explanation の正式データフロー:

```text
analysis/prediction/scenario_latest.json
↓
explanation build
↓
analysis/explanation/scenario_explanation_latest.json
↓
app/static/prediction.html
```

Signal explanation の正式データフロー:

```text
analysis/prediction/signal_latest.json
↓
explanation build
↓
analysis/explanation/signal_explanation_latest.json
↓
app/static/prediction.html
```

FX explanation の正式データフロー:

```text
data/fx/fx_decision_latest*.json
or normalized FX analysis artifact
↓
explanation build
↓
analysis/explanation/fx_explanation_latest.json
↓
app/static/overlay.html
```

World explanation の正式データフロー:

```text
daily_summary_latest.json
+
sentiment_latest.json
+
digest / world summary artifacts
↓
explanation build
↓
analysis/explanation/world_explanation_latest.json
↓
app/static/index.html
```

---

# Fallback Rules

## General Rule

fallback は UI 表示継続のための保険であり、
正式データの代替ではない。

## Digest Fallback Priority

```text
1. data/digest/view_model_latest.json
2. data/world_politics/analysis/daily_summary_latest.json
3. data/world_politics/analysis/daily_news_latest.json
```

## Sentiment Fallback Priority

```text
1. data/world_politics/analysis/sentiment_latest.json
2. data/world_politics/analysis/daily_news_latest.json
```

## Overlay Image Fallback Priority

```text
JPYTHB:
1. /data/fx/fx_overlay_latest_jpythb.png
2. /data/fx/jpy_thb_remittance_overlay.png
3. /data/fx/fx_jpy_thb_overlay.png

USDJPY:
1. /data/fx/fx_overlay_latest_usdjpy.png
2. /data/fx/fx_jpy_usd_overlay.png

USDTHB:
1. /data/fx/fx_overlay_latest_usdthb.png
2. /data/fx/fx_multi_usd_thb_overlay.png

MULTI:
1. /data/fx/fx_overlay_multi_latest.png
2. /data/fx/fx_multi_overlay.png
```

## Overlay Decision Fallback Priority

```text
1. /data/fx/fx_decision_latest_<pair>.json
2. /data/fx/fx_decision_latest.json
```

## Prediction Fallback Priority

```text
1. analysis/prediction/prediction_latest.json
2. no fallback for core prediction content
```

補足:

* Global Status 用の補助表示だけは digest / summary / sentiment / fx latest を読んでよい
* ただし本体の scenario / confidence / watchpoints は prediction latest なしで捏造しない

## Prediction History Fallback Priority

```text
1. analysis/prediction/history/*/prediction.json
2. if history empty, show unavailable state
```

補足:

* History 本文に `prediction_latest.json` を代用しない
* 履歴が無い場合は empty state を表示する

## Thumbnail Fallback Priority

```text
1. image
2. urlToImage
3. thumbnail
4. favicon
5. placeholder
```

---

# Explanation Fallback Rules

## General Rule

explanation fallback は UI 表示継続のための保険であり、
prediction / scenario / signal / fx / world の正式 source を置き換えない。

## Home Explanation Fallback Priority

```text
1. analysis/explanation/world_explanation_latest.json
2. no fallback for structured world explanation
3. if unavailable, show normal summary without explanation block
```

## Overlay Explanation Fallback Priority

```text
1. analysis/explanation/fx_explanation_latest.json
2. do not synthesize explanation from decision JSON
3. if unavailable, display short reason only
```

## Prediction Explanation Fallback Priority

```text
1. analysis/explanation/prediction_explanation_latest.json
2. no fallback for structured prediction explanation
3. if unavailable, display prediction core content without explanation block
```

## Scenario Explanation Fallback Priority

```text
1. analysis/explanation/scenario_explanation_latest.json
2. no fallback
```

## Signal Explanation Fallback Priority

```text
1. analysis/explanation/signal_explanation_latest.json
2. no fallback
```

## Prediction History Explanation Fallback Priority

```text
1. history-local explanation artifact if it exists
2. otherwise no explanation block
3. do not reuse latest explanation as historical explanation
```

## Explanation Empty State Rule

explanation artifact が取得不能な場合は:

```text
unavailable
or non-render
```

のどちらかで扱う。

禁止事項:

```text
prediction_latest.json の内容を explanation のように見せる
UI 側で headline / why_it_matters / must_not_mean を生成する
history explanation が無いのに latest explanation を流用する
```

---

# Design Rules

UI データ依存の原則:

```text
UI は analysis / digest latest / fx latest を読む
scripts は UI を知らない
data は壊れても再生成できる
UI は再計算しない
UI は意味を再発明しない
UI は explanation を再生成しない
```

つまり:

```text
analysis = SST
digest view_model = Digest UI 用の正規化済み表示レイヤ
overlay fallback = 表示継続のための read-only 補助
prediction latest = Prediction UI の正式 runtime output
prediction history = Prediction History UI の正式 review source
explanation latest = UI explanation 表示用の正式構造化説明 artifact
UI meaning layer = UI 用語の定義固定レイヤ
```

---

# UI Meaning Layer

この章は、UI に表示される主要用語の意味を固定する。

目的:

* ページごとの言葉のぶれを防ぐ
* Tooltip / detail / help panel の説明を統一する
* AI や人間が同じ意味で UI を読むための辞書にする
* 「何を意味するか」だけでなく「何を意味しないか」も固定する

重要原則:

```text
意味は analysis / artifact に紐づく
UI は意味を計算しない
UI は意味を脚色しない
tooltip はこの辞書に従う
```

---

## Meaning Layer Rules

### 1. Meaning Source Rule

各用語は可能な限り source artifact と source field を持つこと。

### 2. No UI-Side Redefinition

UI 側で独自に意味説明を書き換えてはならない。

### 3. Must-Not Rule

誤解しやすい用語は
「何を意味しないか」を明記すること。

### 4. Fallback Meaning Rule

fallback 表示中でも、
元の用語の意味を勝手に変更してはならない。

### 5. Page Consistency Rule

同じ用語はページが違っても同じ意味で使うこと。

### 6. Explanation Source Rule

explanation 関連語は
prediction / scenario / signal / fx / world の既存 artifact と
対応する explanation artifact に紐づけること。

### 7. No Fabricated Explanation Rule

explanation artifact が無い場合、
UI は explanation 用語を新規生成してはならない。

---

# Meaning Dictionary

---

## as_of

* Label:
  As Of
* Domain:
  Global / Prediction / History / Explanation
* Definition:
  UI が現在表示しているデータ snapshot の基準日時
* Why it matters:
  ユーザーが「いつ時点の内容か」を誤解しないため
* Source artifact:
  various latest / history / explanation artifacts
* Source field(s):
  as_of
* Used in UI:
  Prediction / Prediction History / Explanation / 共通 status 補助表示
* Allowed values:
  date or datetime string
* Display rule:
  可能な限り明示表示する
* Must not be interpreted as:
  現在時刻 / リアルタイム値 / 市場の最新 tick
* Fallback behavior:
  値が無ければ unknown または unavailable を表示
* Notes:
  updated とは意味が異なる

---

## updated

* Label:
  Updated
* Domain:
  Global
* Definition:
  artifact 自体が最後に更新または生成された時刻
* Why it matters:
  ファイルの鮮度確認に使うため
* Source artifact:
  various latest artifacts
* Source field(s):
  updated / generated_at
* Used in UI:
  header / status / meta 表示
* Allowed values:
  datetime string
* Display rule:
  as_of がある場合でも updated と混同しない
* Must not be interpreted as:
  イベント発生時刻 / 相場変動時刻 / 記事公開時刻
* Fallback behavior:
  値が無ければ unknown
* Notes:
  as_of は観測基準時刻、updated は成果物更新時刻

---

## global_risk

* Label:
  Global Risk
* Domain:
  Home / Global Status / Prediction support
* Definition:
  analysis 層が出した全体状況のリスク水準を要約した表示値
* Why it matters:
  まず何を警戒すべきかを短時間で把握できる
* Source artifact:
  page-specific latest artifact or global status mapping source
* Source field(s):
  global_risk / overall_risk / risk related mapped field
* Used in UI:
  Home / Prediction / Prediction History / 共通 status
* Allowed values:
  low / moderate / high / guarded / unknown
* Display rule:
  共通 status で短く表示し、必要なら detail で補足する
* Must not be interpreted as:
  将来保証 / 確率そのもの / 投資判断の断定
* Fallback behavior:
  source が無い場合は unknown
* Notes:
  ページごとの補助 overview であり、本体ページの source of truth を置き換えない

---

## health

* Label:
  Data Health
* Domain:
  System
* Definition:
  データ完全性、生成成功度、欠損状況などのシステム健全性を示す状態
* Why it matters:
  UI の表示異常がデータ欠損由来かどうかを即座に判定できる
* Source artifact:
  data/digest/health_latest.json
* Source field(s):
  summary.ok / summary.warn / summary.ng / summary.total / status
* Used in UI:
  Home / Global Status
* Allowed values:
  ok / warn / ng / error / unknown
* Display rule:
  市場意味ではなくシステム状態として表示する
* Must not be interpreted as:
  市況 / 世界情勢 / prediction risk
* Fallback behavior:
  値が取れなければ -- または unknown
* Notes:
  人間の健康や経済健康ではなく、パイプライン健全性である

---

## sentiment

* Label:
  Sentiment
* Domain:
  Sentiment / Digest / Home
* Definition:
  記事群のトーンや感情極性を analysis が分類・集計した結果
* Why it matters:
  当日のニュース空気感を定量・定性の両面で確認できる
* Source artifact:
  data/world_politics/analysis/sentiment_latest.json
  data/digest/view_model_latest.json
* Source field(s):
  sentiment_label / sentiment / summary / today / sentiment_summary
* Used in UI:
  Sentiment / Digest / Home snapshot
* Allowed values:
  positive / negative / neutral / mixed / unknown
* Display rule:
  scripts 側の分類結果を表示し、UI は再分類しない
* Must not be interpreted as:
  price direction / direct trade signal / future guarantee
* Fallback behavior:
  source 欠損時のみ digest / daily_news を補助参照
* Notes:
  記事感情であり、Prediction の scenario とは別概念

---

## positive

* Label:
  Positive
* Domain:
  Sentiment
* Definition:
  記事トーンが比較的前向き、改善的、好材料寄りと分類された状態
* Why it matters:
  sentiment 構成比の一部として使う
* Source artifact:
  sentiment artifacts
* Source field(s):
  sentiment_label / sentiment / positive_count
* Used in UI:
  Sentiment KPI / Digest KPI
* Allowed values:
  label or count
* Display rule:
  count と label を混同しない
* Must not be interpreted as:
  必ず相場上昇 / 必ず世界が安定化
* Fallback behavior:
  unknown
* Notes:
  良いニュース全般を意味するとは限らない

---

## negative

* Label:
  Negative
* Domain:
  Sentiment
* Definition:
  記事トーンが比較的悪化、懸念、悪材料寄りと分類された状態
* Why it matters:
  risk 上昇や不安定化の補助把握に使える
* Source artifact:
  sentiment artifacts
* Source field(s):
  sentiment_label / sentiment / negative_count
* Used in UI:
  Sentiment KPI / Digest KPI
* Allowed values:
  label or count
* Display rule:
  count と label を混同しない
* Must not be interpreted as:
  必ず暴落 / 必ず危機発生
* Fallback behavior:
  unknown
* Notes:
  tone 判定であり future event 断定ではない

---

## neutral

* Label:
  Neutral
* Domain:
  Sentiment
* Definition:
  明確なポジティブ / ネガティブのどちらにも大きく寄らない記事分類
* Why it matters:
  極性の偏りを測る基準になる
* Source artifact:
  sentiment artifacts
* Source field(s):
  sentiment_label / sentiment / neutral_count
* Used in UI:
  Sentiment KPI / Digest KPI
* Allowed values:
  label or count
* Display rule:
  sentiment の一分類として表示
* Must not be interpreted as:
  無意味 / 情報価値が低い
* Fallback behavior:
  unknown
* Notes:
  中立記事でも重要イベントを含み得る

---

## mixed

* Label:
  Mixed
* Domain:
  Sentiment
* Definition:
  良材料と悪材料が同時に含まれ、単純な極性へ寄せにくい分類
* Why it matters:
  相反要素の強い日を認識しやすい
* Source artifact:
  sentiment artifacts
* Source field(s):
  sentiment_label / sentiment / mixed_count
* Used in UI:
  Sentiment KPI / Digest KPI
* Allowed values:
  label or count
* Display rule:
  neutral と混同しない
* Must not be interpreted as:
  分析失敗 / エラー
* Fallback behavior:
  unknown
* Notes:
  混合トーンは複雑な状況の兆候になり得る

---

## unknown

* Label:
  Unknown
* Domain:
  Global
* Definition:
  値が取得できない、未計算、未分類、または schema 上見つからない状態
* Why it matters:
  ユーザーに「未取得」であることを正直に示すため
* Source artifact:
  various
* Source field(s):
  various
* Used in UI:
  all pages
* Allowed values:
  literal unknown / placeholder
* Display rule:
  既知値のふりをしない
* Must not be interpreted as:
  zero / safe / neutral / no issue
* Fallback behavior:
  unknown のまま表示する
* Notes:
  unknown を都合よく他値へ変換しない

---

## summary

* Label:
  Summary
* Domain:
  Home / Digest / Prediction / Explanation
* Definition:
  source artifact が持つ要約テキスト
* Why it matters:
  ページの主要内容を短時間で把握できる
* Source artifact:
  daily_summary_latest.json
  data/digest/view_model_latest.json
  analysis/prediction/prediction_latest.json
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  summary / text_summary / daily_summary
* Used in UI:
  Home / Digest / Prediction / Explanation
* Allowed values:
  text
* Display rule:
  ページ本体 source を優先し、暫定 fallback は明示的に扱う
* Must not be interpreted as:
  全記事全文 / 最終結論 / 未来断定
* Fallback behavior:
  page-specific fallback rules に従う
* Notes:
  Summary はページ文脈によって対象が異なる

---

## highlight

* Label:
  Highlight
* Domain:
  Digest / Home
* Definition:
  全記事から抽出された強調表示用の代表カードまたは主要項目
* Why it matters:
  ユーザーが重要項目へ最短で到達できる
* Source artifact:
  data/digest/view_model_latest.json
* Source field(s):
  sections[].cards[]
* Used in UI:
  Digest / Home Events(today)
* Allowed values:
  card list
* Display rule:
  全件リストとは分離して扱う
* Must not be interpreted as:
  全記事一覧 / 全体件数 / 唯一重要な記事群
* Fallback behavior:
  digest fallback source から暫定構築可
* Notes:
  highlights 件数と article 総数は一致しない場合がある

---

## article

* Label:
  Article
* Domain:
  Sentiment / Digest
* Definition:
  元ニュース記事または記事由来の正規化済み表示単位
* Why it matters:
  KPI や summary の根拠単位になる
* Source artifact:
  daily_news_latest.json
  sentiment_latest.json
  view_model_latest.json
* Source field(s):
  items[] / cards[]
* Used in UI:
  Sentiment / Digest
* Allowed values:
  object
* Display rule:
  article count と highlight count を混同しない
* Must not be interpreted as:
  summary そのもの / scenario そのもの
* Fallback behavior:
  no data / unavailable
* Notes:
  Digest では article が card として正規化される場合がある

---

## fx_signal

* Label:
  FX Signal
* Domain:
  Overlay / FX
* Definition:
  FX 分析系が出した方向性または判断補助の signal
* Why it matters:
  remittance や overlay の判断材料になる
* Source artifact:
  data/fx/fx_decision_latest*.json
* Source field(s):
  decision related fields / status related fields
* Used in UI:
  Overlay
* Allowed values:
  implementation dependent
* Display rule:
  pair ごとの source を優先し、general fallback を使う
* Must not be interpreted as:
  自動売買実行 / 必勝サイン / 確定利益
* Fallback behavior:
  pair-specific → generic fallback
* Notes:
  現状は decision 系 field 群の後方互換吸収を含む

---

## decision

* Label:
  Decision
* Domain:
  Overlay / FX
* Definition:
  FX overlay における最終判断ラベルまたは推奨状態
* Why it matters:
  ユーザーが当日判断を一目で確認できる
* Source artifact:
  data/fx/fx_decision_latest_<pair>.json
  data/fx/fx_decision_latest.json
* Source field(s):
  decision / action / status / recommendation
* Used in UI:
  Overlay
* Allowed values:
  schema dependent
* Display rule:
  取得優先順に従って 1 値を採用
* Must not be interpreted as:
  自動執行 / 絶対推奨 / 将来保証
* Fallback behavior:
  field fallback と file fallback を許可
* Notes:
  旧 schema 吸収のため複数 field を見る

---

## reason

* Label:
  Reason
* Domain:
  Overlay / FX / Prediction
* Definition:
  decision や summary を支える説明文または根拠テキスト
* Why it matters:
  結果だけでなく理由を短く確認できる
* Source artifact:
  fx_decision / prediction artifacts
* Source field(s):
  reason / rationale / message / note / summary
* Used in UI:
  Overlay / Prediction
* Allowed values:
  text
* Display rule:
  取得可能な最短の説明を表示
* Must not be interpreted as:
  完全な分析ログ / 全根拠一覧
* Fallback behavior:
  empty state or unavailable
* Notes:
  reason は narrative 補助であり source of truth 自体ではない

---

## fx_explanation

* Label:
  FX Explanation
* Domain:
  Overlay / FX
* Definition:
  FX decision を人間可読の構造へ変換した説明 artifact
* Why it matters:
  decision の背景と watchpoints を安定表示できる
* Source artifact:
  analysis/explanation/fx_explanation_latest.json
* Source field(s):
  headline / summary / why_it_matters / drivers / watchpoints / must_not_mean
* Used in UI:
  Overlay
* Allowed values:
  structured explanation object
* Display rule:
  explanation artifact がある場合のみ表示する
* Must not be interpreted as:
  UI がその場で作った説明 / 将来保証
* Fallback behavior:
  unavailable or non-render
* Notes:
  short reason とは別物

---

## scenario

* Label:
  Scenario
* Domain:
  Prediction
* Definition:
  現在観測から導かれる将来展開の構造化された仮説分岐
* Why it matters:
  未来の可能性を単一路線でなく複数枝として捉えられる
* Source artifact:
  analysis/prediction/prediction_latest.json
  analysis/prediction/scenario_latest.json
* Source field(s):
  scenarios / dominant_scenario / best_case / base_case / worst_case
* Used in UI:
  Prediction / Prediction History
* Allowed values:
  scenario list or named branches
* Display rule:
  runtime 出力をそのまま読む
* Must not be interpreted as:
  予言 / 確定未来 / 必ず起きる結果
* Fallback behavior:
  prediction latest 無しで捏造しない
* Notes:
  structured future narrative として扱う

---

## dominant_scenario

* Label:
  Dominant Scenario
* Domain:
  Prediction
* Definition:
  現時点で最も支持が強い scenario branch
* Why it matters:
  現在の主仮説を一目で示せる
* Source artifact:
  analysis/prediction/prediction_latest.json
* Source field(s):
  dominant_scenario
* Used in UI:
  Prediction / Prediction History
* Allowed values:
  best_case / base_case / worst_case / custom branch name
* Display rule:
  1 つの主枝として表示する
* Must not be interpreted as:
  唯一可能な未来 / 他シナリオ消滅
* Fallback behavior:
  unavailable
* Notes:
  dominant は current leader であって absolute truth ではない

---

## best_case

* Label:
  Best Case
* Domain:
  Prediction
* Definition:
  分岐群の中で相対的に最も良好な結果側の scenario branch
* Why it matters:
  上振れ可能性を把握できる
* Source artifact:
  prediction artifacts
* Source field(s):
  best_case / scenarios.best
* Used in UI:
  Prediction / Prediction History
* Allowed values:
  probability, weight, branch object, or display label depending on schema
* Display rule:
  schema に応じて読み替えてよいが意味は変えない
* Must not be interpreted as:
  願望 / 楽観バイアス / 推奨
* Fallback behavior:
  unavailable
* Notes:
  base / worst とセットで見る

---

## base_case

* Label:
  Base Case
* Domain:
  Prediction
* Definition:
  現在時点で基準線となる中心的 scenario branch
* Why it matters:
  日次判断の標準線になる
* Source artifact:
  prediction artifacts
* Source field(s):
  base_case / scenarios.base
* Used in UI:
  Prediction / Prediction History
* Allowed values:
  probability, weight, branch object, or display label depending on schema
* Display rule:
  best / worst と並べて表示する
* Must not be interpreted as:
  guaranteed outcome / 最終確定
* Fallback behavior:
  unavailable
* Notes:
  dominant_scenario と一致する場合もある

---

## worst_case

* Label:
  Worst Case
* Domain:
  Prediction
* Definition:
  分岐群の中で相対的に最も悪化側の scenario branch
* Why it matters:
  下振れや危険側の監視に使う
* Source artifact:
  prediction artifacts
* Source field(s):
  worst_case / scenarios.worst
* Used in UI:
  Prediction / Prediction History
* Allowed values:
  probability, weight, branch object, or display label depending on schema
* Display rule:
  警戒指標として目立たせてもよいが誇張しない
* Must not be interpreted as:
  必ず起きる破局 / 確定危機
* Fallback behavior:
  unavailable
* Notes:
  watchpoints とセットで読むと有効

---

## confidence

* Label:
  Confidence
* Domain:
  Prediction / History / Explanation
* Definition:
  現在の signals / scenario / runtime judgment の整合強度または支持度
* Why it matters:
  prediction の確からしさの温度感を示せる
* Source artifact:
  analysis/prediction/prediction_latest.json
  analysis/prediction/history/*/prediction.json
  analysis/explanation/*_explanation_latest.json の ui_terms 補助
* Source field(s):
  confidence / ui_terms[].term / ui_terms[].meaning
* Used in UI:
  Prediction / Prediction History / Tooltip
* Allowed values:
  numeric score or explanatory meaning
* Display rule:
  runtime 出力値をそのまま表示し、意味説明は explanation / meaning layer を使う
* Must not be interpreted as:
  的中確率 / 成功確率 / 絶対確信
* Fallback behavior:
  unavailable
* Notes:
  explainability を高めるために最も誤読防止が必要な用語の一つ

---

## drivers

* Label:
  Drivers
* Domain:
  Prediction / Explanation
* Definition:
  現在の scenario や prediction を支えている主要要因群
* Why it matters:
  なぜその結論になっているかを理解できる
* Source artifact:
  analysis/prediction/prediction_latest.json
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  drivers[]
* Used in UI:
  Prediction / Explanation
* Allowed values:
  list of text or structured items
* Display rule:
  配列整形のみ可
* Must not be interpreted as:
  全原因の完全列挙 / 数理モデル全文
* Fallback behavior:
  empty list / unavailable
* Notes:
  decision reason より広い背景要因

---

## watchpoints

* Label:
  Watchpoints
* Domain:
  Prediction / History / Explanation
* Definition:
  今後 scenario 変化を監視するための注目条件または観測項目
* Why it matters:
  ユーザーが次に何を見るべきか分かる
* Source artifact:
  analysis/prediction/prediction_latest.json
  analysis/prediction/history/*/prediction.json
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  watchpoints[]
* Used in UI:
  Prediction / Prediction History / Explanation
* Allowed values:
  list
* Display rule:
  監視項目として簡潔に見せる
* Must not be interpreted as:
  発生確定イベント / 命令 / 結論
* Fallback behavior:
  empty list / unavailable
* Notes:
  scenario drift の前兆監視に使う

---

## invalidation

* Label:
  Invalidation
* Domain:
  Prediction / Explanation
* Definition:
  現在の scenario や prediction が崩れる条件群
* Why it matters:
  「どこで見立てが外れるか」を明示できる
* Source artifact:
  analysis/prediction/prediction_latest.json
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  invalidation / invalidation[]
* Used in UI:
  Prediction / Explanation
* Allowed values:
  list or text
* Display rule:
  watchpoints と区別して表示する
* Must not be interpreted as:
  直ちに失敗した証拠 / エラー状態
* Fallback behavior:
  empty list / unavailable
* Notes:
  must-not-pretend を防ぐ重要欄

---

## implications

* Label:
  Implications
* Domain:
  Prediction
* Definition:
  現在の prediction から想定される downstream effects
* Why it matters:
  予測が何に影響するかを把握できる
* Source artifact:
  analysis/prediction/prediction_latest.json
* Source field(s):
  implications[]
* Used in UI:
  Prediction
* Allowed values:
  list
* Display rule:
  予測結果の含意として表示
* Must not be interpreted as:
  実際に発生済みの事実
* Fallback behavior:
  empty list / unavailable
* Notes:
  observation ではなく forecast implication

---

## explanation

* Label:
  Explanation
* Domain:
  Prediction / Overlay / Home
* Definition:
  既存の判断結果を人間可読の構造へ変換した artifact
* Why it matters:
  UI が安定して理由と誤読防止を表示できる
* Source artifact:
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  root object
* Used in UI:
  Prediction / Overlay / Home
* Allowed values:
  structured explanation object
* Display rule:
  explanation artifact が存在する時のみ表示する
* Must not be interpreted as:
  新しい真実 / UI の自由作文 / 予測本体
* Fallback behavior:
  unavailable or non-render
* Notes:
  prediction 本体の代替ではない

---

## headline

* Label:
  Headline
* Domain:
  Explanation
* Definition:
  explanation artifact の短い一文要約
* Why it matters:
  説明の結論を短時間で把握できる
* Source artifact:
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  headline
* Used in UI:
  Explanation panel / detail section / help drawer
* Allowed values:
  short text
* Display rule:
  summary の前に短く表示する
* Must not be interpreted as:
  記事見出し / 速報 / UIが作ったタイトル
* Fallback behavior:
  non-render or unavailable
* Notes:
  explanation 専用の短文ヘッダ

---

## why_it_matters

* Label:
  Why It Matters
* Domain:
  Explanation
* Definition:
  その判断や状況が利用者にとってなぜ重要かを示す説明
* Why it matters:
  結果の意味と運用上の重要性が分かる
* Source artifact:
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  why_it_matters
* Used in UI:
  Explanation panel / detail section
* Allowed values:
  text
* Display rule:
  summary と分離して表示する
* Must not be interpreted as:
  命令 / 投資助言の断定 / UIの感想
* Fallback behavior:
  non-render or unavailable
* Notes:
  explanation の中核欄

---

## must_not_mean

* Label:
  Must Not Mean
* Domain:
  Explanation / Tooltip
* Definition:
  誤解してはいけない意味を明示するための否定的定義
* Why it matters:
  confidence や prediction の誤読を防げる
* Source artifact:
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  must_not_mean[]
* Used in UI:
  Explanation panel / tooltip / help drawer
* Allowed values:
  list
* Display rule:
  誤解防止欄として分離表示してよい
* Must not be interpreted as:
  エラー一覧 / 不具合報告
* Fallback behavior:
  empty list or non-render
* Notes:
  meaning layer の must-not と思想的に接続する

---

## ui_terms

* Label:
  UI Terms
* Domain:
  Explanation / Tooltip
* Definition:
  UI 上の主要用語に対する文脈依存の意味説明
* Why it matters:
  同じ語でも Prediction 文脈の意味を明確にできる
* Source artifact:
  analysis/explanation/*_explanation_latest.json
* Source field(s):
  ui_terms[]
* Used in UI:
  Tooltip / help drawer / detail panel
* Allowed values:
  list of term-meaning objects
* Display rule:
  tooltip はこの配列または Meaning Dictionary を使う
* Must not be interpreted as:
  UIがその場で再定義した辞書
* Fallback behavior:
  Meaning Dictionary を優先参照し explanation 側は非表示でもよい
* Notes:
  文脈補足として使う

---

## drift

* Label:
  Drift
* Domain:
  Prediction History
* Definition:
  過去 snapshot と現在 snapshot の間で観測される変化量またはずれ
* Why it matters:
  prediction がどう変化したかを時系列で追える
* Source artifact:
  analysis/prediction/history/*/prediction.json
  UI comparison result
* Source field(s):
  overall_risk / confidence / scenario related fields
* Used in UI:
  Prediction History
* Allowed values:
  presentation-level comparison result
* Display rule:
  表示比較として扱い、元値を再定義しない
* Must not be interpreted as:
  prediction engine の再計算結果 / 故障 / 失敗確定
* Fallback behavior:
  履歴不足時は unavailable
* Notes:
  drift は history review の表示概念であり SST そのものではない

---

## risk drift

* Label:
  Risk Drift
* Domain:
  Prediction History
* Definition:
  overall_risk が過去から現在へどう変わったかを示す表示差分
* Why it matters:
  警戒感の上昇 / 低下を時系列で見られる
* Source artifact:
  prediction history snapshots
* Source field(s):
  overall_risk
* Used in UI:
  Prediction History
* Allowed values:
  presentation diff
* Display rule:
  before → after 比較に留める
* Must not be interpreted as:
  新しい risk 計算式
* Fallback behavior:
  unavailable
* Notes:
  derived presentation だが再分析ではない

---

## confidence drift

* Label:
  Confidence Drift
* Domain:
  Prediction History
* Definition:
  confidence が過去から現在へどう変わったかを示す表示差分
* Why it matters:
  主仮説の支持度変化を確認できる
* Source artifact:
  prediction history snapshots
* Source field(s):
  confidence
* Used in UI:
  Prediction History
* Allowed values:
  presentation diff
* Display rule:
  raw confidence との差を分かりやすく示す
* Must not be interpreted as:
  的中率改善の証明
* Fallback behavior:
  unavailable
* Notes:
  confidence の意味自体は変えない

---

## scenario shift

* Label:
  Scenario Shift
* Domain:
  Prediction History
* Definition:
  dominant_scenario または scenario balance が変化したことを示す review 表示
* Why it matters:
  見立ての中心が変わったタイミングを掴める
* Source artifact:
  prediction history snapshots
* Source field(s):
  dominant_scenario / best_case / base_case / worst_case
* Used in UI:
  Prediction History
* Allowed values:
  text or presentation marker
* Display rule:
  変化の有無を簡潔に示す
* Must not be interpreted as:
  engine bug / データ破損
* Fallback behavior:
  unavailable
* Notes:
  scenario balance 変化を説明する review 用語

---

## unavailable

* Label:
  Unavailable
* Domain:
  Global
* Definition:
  必要な artifact または field が取得できず、表示内容を構築できない状態
* Why it matters:
  欠損と既知値を区別できる
* Source artifact:
  various
* Source field(s):
  n/a
* Used in UI:
  all pages
* Allowed values:
  literal unavailable / empty state
* Display rule:
  no data と誠実に表示する
* Must not be interpreted as:
  zero / safe / same as previous
* Fallback behavior:
  empty state
* Notes:
  unknown より強い「非利用可能」表示として使う場合がある

---

## loading

* Label:
  Loading
* Domain:
  Global
* Definition:
  データ取得または描画処理の途中状態
* Why it matters:
  一時的未表示と恒久欠損を区別できる
* Source artifact:
  n/a
* Source field(s):
  n/a
* Used in UI:
  all pages
* Allowed values:
  transient state
* Display rule:
  final valueのふりをしない
* Must not be interpreted as:
  unavailable / unknown / error
* Fallback behavior:
  timeout 後は unavailable or error state
* Notes:
  runtime fetch 状態の表示語

---

## fallback

* Label:
  Fallback
* Domain:
  Global / UI behavior
* Definition:
  正式 source が取得不能なとき、表示継続のために用いる代替参照または代替表示
* Why it matters:
  UI を落とさず、かつ source of truth を偽装しないため
* Source artifact:
  page-specific fallback candidates
* Source field(s):
  page-specific
* Used in UI:
  all pages where allowed
* Allowed values:
  candidate file / field / placeholder
* Display rule:
  保険としてのみ使う
* Must not be interpreted as:
  正式 source の置き換え / 新しい真実
* Fallback behavior:
  documented priority に従う
* Notes:
  fallback は表示継続専用

---

# Meaning Layer Integration Guidance

この Meaning Layer は将来的に以下へ接続してよい:

```text
tooltip
detail panel
help drawer
page explanation section
generated explanation artifact
```

ただし重要原則:

```text
UI は意味辞書を勝手に再編集しない
scripts / docs 側で定義した意味を読む
```

将来、必要であれば explanation artifact を生成してもよい。
例:

```text
analysis/ui/explanation_dictionary_latest.json
```

ただしその場合も、
意味の上位定義は本ドキュメントと整合していなければならない。

---

# Explanation Layer Integration Guidance

Explanation Layer は UI Meaning Layer と近いが、同一ではない。

違い:

```text
Meaning Layer
= UI 用語の意味辞書

Explanation Layer
= 各判断結果を人間可読構造へ変換した artifact
```

関係:

```text
prediction_latest.json
↓
prediction_explanation_latest.json
↓
Prediction UI explanation section

scenario_latest.json
↓
scenario_explanation_latest.json
↓
Prediction UI scenario explanation section

signal_latest.json
↓
signal_explanation_latest.json
↓
Prediction UI signal explanation section

fx_decision_latest*.json
↓
fx_explanation_latest.json
↓
Overlay UI explanation section

world summary artifacts
↓
world_explanation_latest.json
↓
Home UI explanation section
```

重要原則:

```text
Meaning Layer は定義
Explanation Layer は文脈付き説明
UI は両方を読むが再生成しない
```

UI 実装ルール:

1. explanation block は artifact が存在する時だけ表示する
2. explanation block の headline / summary / why_it_matters は explanation artifact を正とする
3. tooltips は Meaning Dictionary を優先し、必要時のみ ui_terms を補助参照する
4. explanation の must_not_mean は誤読防止欄として使ってよい
5. explanation artifact が無い場合、通常の prediction / overlay / home 本体だけ表示してよい
6. explanation artifact が無いからといって UI が explanation 文を生成してはならない

---

# Relation to Layout Standard

UI 依存は、標準レイアウトと切り離して考えない。
現行の主要ページは、以下の共通骨格を前提とする。

```text
#site-header
.container
.page content
#site-footer
/static/common/layout.js
```

また、標準の主要ナビゲーションは以下で固定する。

```text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

重要:

* レイアウト共通化は表示構造の統一であり、データ依存の共通化ではない
* 各ページは同じ骨格を持っても、読む JSON / PNG / history source は異なる
* explanation を追加しても layout 側で意味計算をしない
* データ依存を変更したら `docs/ui_data_dependencies.md` を更新する
* レイアウト標準を変更したら `docs/ui_layout_standard.md` を更新する
* 意味定義を追加・変更した場合も `docs/ui_data_dependencies.md` を更新する

---

# When Updating UI

UI 変更時は必ず確認すること:

1. 参照 JSON / PNG は何か
2. その root structure は何か
3. 必要 field は何か
4. fallback はどこまで許すか
5. explanation artifact を読むか
6. explanation が無いとき non-render でよいか
7. layout standard と矛盾していないか
8. 用語の意味が本ドキュメントと一致しているか
9. docs/ui_data_dependencies.md を更新したか
10. 必要なら docs/ui_layout_standard.md も更新したか

特に Digest を変更する場合は、
以下の整合を必ず確認する:

```text
build_daily_sentiment.py
build_digest_view_model.py
data/digest/view_model_latest.json
app/static/digest.html
```

特に Overlay を変更する場合は、
以下の整合を必ず確認する:

```text
data/fx/
pair-specific latest files
fx_decision_latest.json
analysis/explanation/fx_explanation_latest.json
app/static/overlay.html
```

特に Prediction を変更する場合は、
以下の整合を必ず確認する:

```text
prediction runtime
analysis/prediction/prediction_latest.json
analysis/explanation/prediction_explanation_latest.json
analysis/explanation/scenario_explanation_latest.json
analysis/explanation/signal_explanation_latest.json
app/static/prediction.html
```

特に Prediction History を変更する場合は、
以下の整合を必ず確認する:

```text
analysis/prediction/history/
window scan logic
optional history-local explanation
app/static/prediction_history.html
```

特に Home explanation を変更する場合は、
以下の整合を必ず確認する:

```text
daily_summary_latest.json
sentiment_latest.json
analysis/explanation/world_explanation_latest.json
app/static/index.html
```

---

# Troubleshooting Hints

## Symptom: Digest で unknown が全件になる

確認順:

```text
1. sentiment_latest.json に sentiment_label があるか
2. view_model_latest.json の cards[].sentiment があるか
3. digest.html が view_model_latest.json を読んでいるか
4. ブラウザキャッシュを疑う
```

## Symptom: KPI は正しいが Top highlights が少ない

考えられる原因:

```text
cards[] は highlights 抽出結果
sentiment_summary.articles は全件
```

これは仕様であり得る。

## Symptom: サムネイルが favicon になる

確認順:

```text
1. view_model_latest.json の cards[].image
2. digest builder で daily_news の画像が引き継がれているか
3. UI fallback が favicon に落ちていないか
```

## Symptom: Overlay で USDTHB が出ない

確認順:

```text
1. /data/fx/fx_overlay_latest_usdthb.png が存在するか
2. 無ければ /data/fx/fx_multi_usd_thb_overlay.png が存在するか
3. /data/fx/fx_decision_latest_usdthb.json が存在するか
4. 無ければ /data/fx/fx_decision_latest.json を fallback しているか
5. ブラウザキャッシュを疑う
```

## Symptom: Prediction explanation が出ない

確認順:

```text
1. analysis/explanation/prediction_explanation_latest.json が存在するか
2. headline / summary / why_it_matters があるか
3. prediction.html が explanation artifact を読んでいるか
4. UI が prediction_latest から explanation を作ろうとしていないか
5. ブラウザキャッシュを疑う
```

## Symptom: Scenario explanation が出ない

確認順:

```text
1. analysis/explanation/scenario_explanation_latest.json が存在するか
2. scenario section が optional render になっているか
3. UI が no fallback を守っているか
```

## Symptom: FX explanation が出ない

確認順:

```text
1. analysis/explanation/fx_explanation_latest.json が存在するか
2. overlay.html が reason と explanation を混同していないか
3. explanation 無し時に short reason だけ表示しているか
```

## Symptom: Home explanation が出ない

確認順:

```text
1. analysis/explanation/world_explanation_latest.json が存在するか
2. index.html が normal summary と explanation block を分離しているか
3. explanation 無し時に本文まで消していないか
```

## Symptom: Data Health で OK/WARN/NG が -- になる

確認順:

```text
1. health_latest.json に summary があるか
2. summary.ok / warn / ng / total があるか
3. Home が health.summary.* を読んでいるか
```

## Symptom: Prediction で scenario / confidence が出ない

確認順:

```text
1. analysis/prediction/prediction_latest.json が存在するか
2. core fields が schema 上どこにあるか
3. prediction.html が latest prediction を読んでいるか
4. UI が fallback で埋めようとしていないか
5. ブラウザキャッシュを疑う
```

## Symptom: Prediction History で history が空になる

確認順:

```text
1. analysis/prediction/history/*/prediction.json があるか
2. 日付ディレクトリが期待形式か
3. latest 7 / latest 30 の window 条件が厳しすぎないか
4. prediction_history.html が latest ではなく history を読んでいるか
5. ブラウザキャッシュを疑う
```

## Symptom: Global Status が縦に伸びすぎる

確認順:

```text
1. 5-card 横並び構造になっているか
2. page-specific text dump になっていないか
3. 他ページと同じ Global Status component / style を使っているか
```

## Symptom: Tooltip の説明がページごとに違う

確認順:

```text
1. 説明文が UI 側に直書きされていないか
2. 本ドキュメントの Meaning Dictionary と一致しているか
3. 同じ語に別ラベルを与えていないか
4. 一部ページだけ独自説明を追加していないか
5. ui_terms が Meaning Dictionary を上書きしていないか
```

---

# Future Expansion

将来 UI 依存として追加される可能性:

```text
trend3
signals
scenario
prediction
risk_score
regime
observation
overlay_related_news
prediction review notes
scenario change log
historical_pattern
historical_analog
pattern_confidence
analog_confidence
explanation artifact
tooltip registry
detail panel registry
history-local explanation
multi-language explanation fields
```

これらが UI に追加された場合、
本ドキュメントへ依存関係と意味定義を必ず記録する。

---

END OF DOCUMENT

```
