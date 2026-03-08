# Analysis Data Schema
GenesisPrediction v2

Status: Active  
Purpose: analysis データ構造の定義  
Last Updated: 2026-03-06

---

# 0. Purpose

このドキュメントは

```

analysis/

```

ディレクトリの **データ構造（schema）** を記録する。

目的

- AIがデータ構造を即理解できるようにする
- UI改修時の探索コストをゼロにする
- pipeline修正時の事故を防ぐ

GenesisPrediction v2 の真実は

```

analysis/

```

のみである。

---

# 1. World Politics

Directory

```

analysis/world_politics/

```

---

## daily_news_latest.json

ニュース記事一覧

Fields

```

title
source
publishedAt
url
urlToImage
description
content

```

Purpose

```

ニュースのrawデータ

```

---

## sentiment_latest.json

ニュース記事の sentiment 分類

Fields

```

title
source
publishedAt
url
urlToImage
sentiment

```

sentiment values

```

positive
negative
neutral
mixed
unknown

```

Purpose

```

Sentimentページ
KPIカウント
記事一覧

```

---

## daily_summary_latest.json

ニュース要約

Fields

```

as_of
summary
risk_score
topics

```

Purpose

```

Homeページ
Digestページ

```

---

# 2. Digest

Directory

```

analysis/digest/

```

---

## view_model_latest.json

Digest UI 用の集計データ

Fields

```

as_of
kpi
articles
highlights

```

kpi example

```

positive
negative
neutral
mixed

```

articles example

```

title
url
urlToImage
sentiment
risk_score

```

Purpose

```

digest.html

```

---

# 3. FX

Directory

```

analysis/fx/

```

---

## fx_overlay_latest.png

FX overlay visualization

Purpose

```

overlay.html

```

---

## remittance dashboard CSV

Example

```

jpy_thb_remittance_dashboard.csv
usd_jpy_dashboard.csv

```

Purpose

```

送金判断

```

---

# 4. Health

Directory

```

analysis/

```

---

## health_latest.json

Pipeline health 状態

Fields

```

OK
WARN
NG

```

Purpose

```

Data health monitoring

```

---

# 5. Design Rule

GenesisPrediction のデータ設計

```

data → 素材
scripts → 生成
analysis → 真実
UI → 表示

```

UI は

```

analysis

```

のみ読む。

---

# 6. When Schema Changes

analysis の構造が変わった場合

```

必ずこのファイルを更新する

```

---

# 7. Future Expansion

予定

```

trend3
signals
scenario
prediction
risk_model

```

追加された場合

```

analysis_data_schema.md

```

に追記する。

---

END OF DOCUMENT
```
