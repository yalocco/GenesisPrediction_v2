# Global Status Data Mapping
GenesisPrediction v2

Version: 1.0  
Status: Active  
Location: docs/core/ui/

---

# 1. Purpose

この文書は

**Global Status コンポーネントに表示する情報の意味をページごとに固定する**

ための標準定義である。

GenesisPrediction UI では Global Status は

- 全ページ共通
- 5カード固定
- DOM固定
- CSS固定

のコンポーネントとして定義されている。

しかしカードの「意味」はページごとに異なるため、
この文書で **カードの意味とデータソースを固定する。**

これにより

- UI意味のブレを防ぐ
- AIがカード内容を誤解するのを防ぐ
- 新しいページ追加時の設計基準を作る

---

# 2. Global Status Structure

Global Status は常に **5カード構造**を持つ。

```text
Card 1
Card 2
Card 3
Card 4
Card 5
````

原則

* カード数変更禁止
* DOM順序変更禁止
* CSS構造変更禁止
* カード意味変更はこの文書を更新する

---

# 3. Common Card

すべてのページで **Card 1 は Date を表示する。**

```text
Card 1
Date
```

意味

```
World Date
Analysis Date
Observation Date
```

データソース

```
analysis/
daily_summary_latest.json
```

例

```
2026-03-09
```

---

# 4. Home Page Mapping

Home は **システム全体状況の Overview ページ**である。

```text
Card 1
Date

Card 2
System

Card 3
Analysis

Card 4
Prediction

Card 5
Health
```

意味

### System

GenesisPrediction runtime 状態

例

```
Morning Ritual
Pipeline status
Last update
```

---

### Analysis

analysis pipeline 状態

例

```
News ingestion
Sentiment
Digest generation
```

---

### Prediction

prediction engine 状況

例

```
Prediction available
Last prediction date
Regime classification
```

---

### Health

データ整合性

例

```
Health OK
Missing data
Pipeline error
```

---

# 5. Overlay Page Mapping

Overlay は **FX Overlay / FX判断ページ**である。

```text
Card 1
Date

Card 2
FX Base

Card 3
FX Signal

Card 4
Trend

Card 5
Health
```

意味

### FX Base

基準為替

例

```
USDJPY
JPYTHB
```

---

### FX Signal

FX判断

例

```
ON
WARN
OFF
```

---

### Trend

トレンド

例

```
Uptrend
Downtrend
Sideways
```

---

### Health

FXデータ状態

例

```
API OK
Fallback active
Data missing
```

---

# 6. Sentiment Page Mapping

Sentiment は **ニュース感情分析ページ**である。

```text
Card 1
Date

Card 2
Articles

Card 3
Positive

Card 4
Negative

Card 5
Health
```

意味

### Articles

記事数

例

```
Total articles analyzed
```

---

### Positive

ポジティブ記事割合

---

### Negative

ネガティブ記事割合

---

### Health

sentiment pipeline 状態

---

# 7. Digest Page Mapping

Digest は **ニュース要約ページ**である。

```text
Card 1
Date

Card 2
Articles

Card 3
Highlights

Card 4
Risk

Card 5
Health
```

意味

### Articles

取得記事数

---

### Highlights

重要記事数

---

### Risk

リスク記事数

---

### Health

digest pipeline 状態

---

# 8. Prediction Page Mapping

Prediction は **最新予測表示ページ**である。

```text
Card 1
Date

Card 2
Regime

Card 3
Signal

Card 4
Confidence

Card 5
Health
```

意味

### Regime

世界情勢分類

例

```
Stable
Tension
Crisis
Transition
```

---

### Signal

予測シグナル

例

```
Low risk
Elevated risk
High risk
```

---

### Confidence

予測信頼度

例

```
0.72
72%
```

---

### Health

prediction engine 状態

---

# 9. Prediction History Mapping

Prediction History は **予測履歴ページ**である。

```text
Card 1
Date

Card 2
Snapshots

Card 3
Drift

Card 4
Review

Card 5
Health
```

意味

### Snapshots

保存済み予測数

---

### Drift

前回予測との差

---

### Review

レビュー状況

---

### Health

history data 状態

---

# 10. Data Source Principles

Global Status は **軽量サマリー表示**のみを行う。

原則

* 重い計算禁止
* API呼び出し禁止
* DOM再生成禁止
* JavaScriptは値差し込みのみ

データは

```
analysis/
daily_summary_latest.json
analysis/
prediction_latest.json
analysis/
health_latest.json
```

などの **既存サマリーJSON**から取得する。

---

# 11. Change Rules

Global Status の意味を変更する場合

必ず

```
docs/core/ui/global_status_data_mapping.md
```

を更新する。

更新なしのUI変更は禁止。

---

# 12. Relationship to Other UI Standards

関連文書

```
ui_design_philosophy.md
ui_component_catalog.md
ui_layout_standard.md

global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
```

役割

```
Design philosophy
Component catalog
Layout standard
Global Status component
Global Status HTML
Global Status CSS
Global Status data mapping
```

---

# 13. Definition of Done

Global Status が標準準拠とみなされる条件

* 全ページで5カード構造
* Card 1 は Date
* カード意味がこの文書と一致
* DOM変更無し
* CSS変更無し
* JSは値差し込みのみ

---

END OF DOCUMENT

````
