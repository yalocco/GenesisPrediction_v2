# UI Data Dependencies

GenesisPrediction v2

Version: 1.4
Status: Active
Purpose: UI がどのデータを読むか、どの field に依存するか、fallback をどう扱うかを固定する
Last Updated: 2026-03-08

---

# Overview

このドキュメントは、GenesisPrediction v2 の UI とデータ依存関係を記録する。

目的:

- AI が毎回データ構造を探し直すことを防ぐ
- UI 改修時の事故を防ぐ
- fallback 挙動を明文化する
- scripts / analysis / UI の責務を分離して保つ
- 統一済み UI レイアウトとデータ依存を対応づける

重要原則:

```text
scripts → analysis を生成
analysis → Runtime SST
UI → analysis を読む
UI は再計算しない
```

つまり

```text
analysis = Single Source of Truth
```

UI 側でロジックを持つ場合も、それは表示や fallback のみであり、
分析値そのものの決定は scripts / analysis 側で行う。

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
```

補足:

- 全主要ページは共通 header / footer / layout.js を使う
- レイアウト標準は `docs/ui_layout_standard.md` に従う
- UI は data / analysis の latest または history を読む read-only レイヤである

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
```

## Notes

- Home は集約表示ページ
- Summary は `daily_summary_latest.json` を優先参照する
- Events(today) は `data/digest/view_model_latest.json` の highlights / cards を使う
- Data Health は `health_latest.json.summary.ok / warn / ng / total` を使う
- Sentiment snapshot は Sentiment ページと揃えるため `data/world_politics/analysis/sentiment_latest.json` を優先参照する
- 詳細分析は Sentiment / Digest / Overlay / Prediction 側で行う
- latest alias の鮮度が重要

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

- 現在の repo では `fx_overlay_latest_usdthb.png` が存在しない場合がある
- その場合 Overlay UI は `fx_multi_usd_thb_overlay.png` を fallback として使う

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

- 現在の repo では `fx_decision_latest_usdthb.json` が存在しない場合がある
- その場合 Overlay UI は `fx_decision_latest.json` を fallback として使う

### MULTI

```text
/data/fx/fx_decision_latest_multi.json
/data/fx/fx_decision_latest.json
```

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

## Notes

- Overlay は FX 判断系の表示ページ
- 主 source は `data/fx/`
- UI は fallback を行うが、正式な latest 命名・pair 別成果物の整備は scripts 側責務
- `USDTHB` は現状 fallback 表示で動作するが、将来的には pair-specific latest の生成が望ましい
- 詳細仕様は docs/ui_system.md と docs/pipeline_system.md に従う

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

- Sentiment page は per-article sentiment 表示が主目的
- score / net / risk / positive / uncertainty の表示は UI 側で再計算しない
- label の判定は scripts/build_daily_sentiment.py 側を正とする

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

- `cards[]` は Top highlights 用の抽出結果
- `sentiment_summary.articles` は全 article 件数

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

- risk / score は card.sentiment 側の値を利用
- UI は再計算しない
- 並び替えは表示順の変更のみ

## Sentiment Label Handling

Digest card の label は以下優先順で読む:

```text
card.sentiment.sentiment_label
card.sentiment.sentiment
card.sentiment.label
```

card 直下に同名 field が存在する旧 schema にも、可能な限り後方互換対応してよい。

## Notes

- Digest の正式 source は `view_model_latest.json`
- `daily_news_latest.json` は fallback 用
- `unknown` が大量発生する場合は、まず `view_model_latest.json` の `cards[].sentiment` を確認する
- KPI が cards 件数と一致しない場合、`sentiment_summary` を見て仕様通りか判断する
- 現行 UI では Highlights は KPI 表示専用であり、記事カードは Articles セクションへ集約する

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

- 実 runtime schema は進化してよい
- UI は後方互換的に複数 field 名を拾ってよい
- ただし UI が確率や risk を独自再計算してはならない

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

## Notes

- Prediction は runtime output の可視化ページ
- 正式 source は `analysis/prediction/prediction_latest.json`
- Global Status は共通UI用の補助表示であり、Prediction判定そのものではない
- ボタンで JSON を開く場合も、prediction latest を最優先とする

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

- これは表示比較であり、分析再計算ではない
- 元 snapshot の値を加工しすぎない
- 過去値 → 現在値の比較表示に留める

## Notes

- Prediction History は時系列 review ページ
- 上部 Global Status は他ページと同型の 5-card 横並びを標準とする
- 本体は history snapshot の比較表示に集中する
- latest と history の schema 差がある場合、UI は後方互換吸収をしてよい

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

- Global Status 用の補助表示だけは digest / summary / sentiment / fx latest を読んでよい
- ただし本体の scenario / confidence / watchpoints は prediction latest なしで捏造しない

## Prediction History Fallback Priority

```text
1. analysis/prediction/history/*/prediction.json
2. if history empty, show unavailable state
```

補足:

- History 本文に `prediction_latest.json` を代用しない
- 履歴が無い場合は empty state を表示する

## Thumbnail Fallback Priority

```text
1. image
2. urlToImage
3. thumbnail
4. favicon
5. placeholder
```

---

# Design Rules

UI データ依存の原則:

```text
UI は analysis / digest latest / fx latest を読む
scripts は UI を知らない
data は壊れても再生成できる
UI は再計算しない
```

つまり:

```text
analysis = SST
digest view_model = Digest UI 用の正規化済み表示レイヤ
overlay fallback = 表示継続のための read-only 補助
prediction latest = Prediction UI の正式 runtime output
prediction history = Prediction History UI の正式 review source
```

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

- レイアウト共通化は表示構造の統一であり、データ依存の共通化ではない
- 各ページは同じ骨格を持っても、読む JSON / PNG / history source は異なる
- データ依存を変更したら `docs/ui_data_dependencies.md` を更新する
- レイアウト標準を変更したら `docs/ui_layout_standard.md` を更新する

---

# When Updating UI

UI 変更時は必ず確認すること:

1. 参照 JSON / PNG は何か
2. その root structure は何か
3. 必要 field は何か
4. fallback はどこまで許すか
5. layout standard と矛盾していないか
6. docs/ui_data_dependencies.md を更新したか
7. 必要なら docs/ui_layout_standard.md も更新したか

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
app/static/overlay.html
```

特に Prediction を変更する場合は、
以下の整合を必ず確認する:

```text
prediction runtime
analysis/prediction/prediction_latest.json
app/static/prediction.html
```

特に Prediction History を変更する場合は、
以下の整合を必ず確認する:

```text
analysis/prediction/history/
window scan logic
app/static/prediction_history.html
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
```

これらが UI に追加された場合、
本ドキュメントへ依存関係を必ず記録する。

---

END OF DOCUMENT
