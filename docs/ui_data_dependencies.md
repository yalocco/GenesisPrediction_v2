はい、わかります 👍
意味はこうです。

あなたの **`docs/ui_data_dependencies.md`** は
「UIがどのJSONを読むか」を固定するドキュメントです。

今回の作業で **Digest の構造が変わりました**。

追加されたもの：

```
sentiment_summary
today.sentiment
today.sentiment_summary
cards[].sentiment
cards[].image
```

なので **Digest依存関係を更新する必要があります。**

そしてこのプロジェクトのルールでは

* 差分ではなく
* **完全ファイル置き換え**

です。 

---

# 更新版

`docs/ui_data_dependencies.md`
（完全置き換え）

```md
# UI Data Dependencies

GenesisPrediction v2

Version: 1.1
Status: Active
Purpose: UIがどのデータを参照しているかを固定化する
Last Updated: 2026-03-06

---

# Overview

このドキュメントは **UIとデータの依存関係**を記録する。

目的：

- AIが毎回データ構造を探すことを防ぐ
- UI改修時の事故を防ぐ
- JSON依存関係を明確化する

重要原則：

```

UIは analysis を読む
scripts は UIを知らない

```

つまり

```

analysis = Single Source of Truth

```

---

# Sentiment Page

File:

```

app/static/sentiment.html

```

---

## Data Source

```

data/world_politics/analysis/sentiment_latest.json

```

---

## KPI

KPIは sentiment 分類結果を表示する。

Fields:

```

positive
negative
neutral
mixed
unknown

```

用途:

```

ページ上部のKPIカウンター表示

```

---

## Article List

記事リストは sentiment エントリから生成する。

Fields:

```

title
source
publishedAt
url
sentiment
risk
positive
uncertainty
net

```

---

## Thumbnail

Thumbnail はニュース画像を表示する。

Primary field:

```

urlToImage

```

Fallback:

```

placeholder image
または非表示

```

目的:

```

記事一覧の視認性向上

```

---

# Digest Page

File:

```

app/static/digest.html

```

---

## Data Source

```

data/digest/view_model_latest.json

```

---

## Root Structure

Digest ViewModel structure:

```

date
generated_at
sections[]
sentiment_summary
today

```

---

## KPI Source

Digest KPI は以下を参照する。

```

sentiment_summary

```

Fields:

```

articles
positive_count
negative_count
neutral_count
mixed_count
unknown_count
net
risk
positive
uncertainty

```

用途:

```

Digestページ上部のKPIカード

```

---

## Article Cards

Digest の Top highlights は

```

sections[].cards[]

```

から生成される。

Fields:

```

title
source
url
image
sentiment
risk
positive
uncertainty
net

```

---

## Sentiment Label

カードには以下の分類が付与される。

```

positive
negative
neutral
mixed
unknown

```

用途:

```

記事カードのラベル表示

```

---

## Thumbnail

Thumbnail source:

```

image

```

Fallback:

```

urlToImage
no-image placeholder

```

目的:

```

ニュース一覧の視認性向上

```

---

# UI Data Flow

Digestデータ生成フロー

```

daily_news
↓
sentiment pipeline
↓
digest view model
↓
digest.html

```

---

# Design Rules

UIデータ依存の原則

```

UIはanalysisを読む
scriptsはUIを知らない
dataは壊れても再生成できる

```

つまり

```

analysis = Single Source of Truth

```

---

# When Updating UI

UI変更時は必ず確認すること

1. 参照JSON
2. 必要field
3. fallback動作

そして

```

このファイルを更新する

```

---

# Future Expansion

将来追加される可能性

```

trend3
signals
risk_score
scenario
prediction

```

これらがUIに追加された場合、

このドキュメントに依存関係を記録する。

---

END OF DOCUMENT
```
