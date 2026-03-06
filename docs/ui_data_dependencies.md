# UI Data Dependencies

GenesisPrediction v2

Version: 1.0
Status: Active
Purpose: UIがどのデータを参照しているかを固定化する
Last Updated: 2026-03-06

---

# Overview

このドキュメントは **UIとデータの依存関係**を記録する。

目的：

* AIが毎回データ構造を探すことを防ぐ
* UI改修時の事故を防ぐ
* JSON依存関係を明確化する

重要：

```text
UIは analysis を読む
scripts は UIを知らない
```

つまり

```
analysis = UIの唯一のデータソース
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

## KPI

Digest KPI はニュース集計結果を表示する。

Typical fields:

```
positive
negative
neutral
mixed
```

用途:

```
Daily sentiment overview
```

---

## Article Thumbnails

Thumbnail source:

```
urlToImage
```

Fallback:

```
no-image placeholder
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
