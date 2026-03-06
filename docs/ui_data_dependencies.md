はい。
**`docs/ui_data_dependencies.md` 完全更新版** をそのまま置き換え用で出します。
今回の Digest の正式依存先が `data/digest/view_model_latest.json` に変わった点と、KPI が `sentiment_summary` を優先する点を反映しています。旧案の方向性は合っていましたが、今回の実動作に合わせて整理し直しました。 

````md
# UI Data Dependencies

GenesisPrediction v2

Version: 1.2
Status: Active
Purpose: UI がどのデータを読むか、どの field に依存するか、fallback をどう扱うかを固定する
Last Updated: 2026-03-06

---

# Overview

このドキュメントは、GenesisPrediction v2 の UI とデータ依存関係を記録する。

目的:

- AI が毎回データ構造を探し直すことを防ぐ
- UI 改修時の事故を防ぐ
- fallback 挙動を明文化する
- scripts / analysis / UI の責務を分離して保つ

重要原則:

```text
scripts → analysis を生成
analysis → Runtime SST
UI → analysis を読む
UI は再計算しない
````

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
```

主要なデータ配置:

```text
data/world_politics/analysis/
data/digest/
data/fx/
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
data/world_politics/analysis/view_model_latest.json
data/world_politics/analysis/daily_summary_latest.json
data/world_politics/analysis/health_latest.json
```

## Notes

* Home は集約表示ページ
* 詳細分析は Sentiment / Digest / Overlay 側で行う
* latest alias の鮮度が重要

---

# Overlay Page

File:

```text
app/static/overlay.html
```

## Primary Purpose

FX / overlay の判断結果を表示する。

## Main Dependencies

代表的な依存先:

```text
data/fx/fx_overlay_latest.json
data/fx/fx_overlay_multi_latest.json
data/world_politics/analysis/view_model_latest.json
```

## Overlay Fields

UI が参照する代表 field:

```text
date
pair
rate
regime
signal
score
decision
reason
image
```

## Notes

* Overlay は FX 判断系の表示ページ
* sentiment の補助利用はあり得るが、主 source は FX 系 latest
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
UI は analysis / digest latest を読む
scripts は UI を知らない
data は壊れても再生成できる
UI は再計算しない
```

つまり:

```text
analysis = SST
digest view_model = Digest UI 用の正規化済み表示レイヤ
```

---

# When Updating UI

UI 変更時は必ず確認すること:

1. 参照 JSON は何か
2. その JSON の root structure は何か
3. 必要 field は何か
4. fallback はどこまで許すか
5. docs/ui_data_dependencies.md を更新したか

特に Digest を変更する場合は、
以下の整合を必ず確認する:

```text
build_daily_sentiment.py
build_digest_view_model.py
data/digest/view_model_latest.json
app/static/digest.html
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
```

これらが UI に追加された場合、
本ドキュメントへ依存関係を必ず記録する。

---

END OF DOCUMENT

````
