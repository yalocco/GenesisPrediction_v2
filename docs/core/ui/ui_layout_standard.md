# GenesisPrediction UI Layout Standard

この文書は GenesisPrediction UI のレイアウト構造を定義する。

目的

- UI構造の統一
- レイアウト崩れ防止
- AI作業時の参照基準
- 新規ページ作成時のテンプレート


---

# UIアーキテクチャ

GenesisPrediction UI は以下の **3層構造** で管理される。

```

Theme Layer
Layout Layer
Page Layer

```

構造

```

Theme
app/static/app.css

Layout
app/static/common/layout.js

Page
app/static/index.html
app/static/overlay.html
app/static/sentiment.html
app/static/digest.html
app/static/prediction.html
app/static/prediction_history.html

```

役割

Theme  
UIデザイン全体

Layout  
header / navigation / footer

Page  
各ページ固有コンテンツ


---

# 共通レイアウト構造

すべてのページは以下の構造を持つ。

```

Header
Hero
Main Content
Panels
Footer

```

例

```

<header>
hero
panel
grid
panel
</main>
<footer>
```

Header / Footer は layout.js が生成する。

---

# Header構造

Header は **layout.js によって自動生成される。**

構造

```
Topbar
Brand
Navigation
Health Status
```

Navigation

```
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

HTML側で Header を個別実装してはいけない。

---

# Heroセクション

ページ最上部の説明領域。

構造

```
Hero Title
Hero Summary
Hero Meta
```

例

```
GenesisPrediction
Global Situation Overview
as_of 2026-03-12
```

---

# Panel構造

UIの基本単位。

```
.panel
```

内容

```
section header
grid
card
list
timeline
```

例

```
.panel
.section-header
.card
```

---

# Grid構造

レスポンシブ対応の基本構造。

```
grid-2
grid-3
stack
```

grid-2

```
2 column
```

grid-3

```
3 column
```

stack

```
vertical list
```

---

# KPI / Metric構造

数値表示コンポーネント。

```
.metric-card
.metric-label
.metric-value
.metric-sub
```

使用例

```
FX Rate
Sentiment Score
Risk Index
```

---

# Global Status構造

システム状態表示。

```
.global-status
.status-card
.status-label
.status-value
.status-sub
```

表示例

```
News
Sentiment
Prediction
FX
System
```

---

# Navigationルール

nav は以下の条件を満たす。

```
固定高さ
固定padding
hover変化あり
active表示あり
```

nav は layout.js が生成する。

---

# Footer構造

Footerは共通。

```
GenesisPrediction v2
UI is read-only
analysis is SST
```

---

# 新規ページ作成ルール

新しいページを作る場合

1
HTMLは content のみ作る

2
Header / Footer は layout.js に任せる

3
CSSは app.css を使用

4
個別CSSは禁止

---

# UI変更ルール

UI変更は必ず

```
app.css
```

から行う。

HTMLの style 編集は禁止。

---

# 既存ページ

GenesisPrediction UI は現在以下のページを持つ。

```
index
overlay
sentiment
digest
prediction
prediction_history
```

---

# この文書の役割

GenesisPrediction UI の

**レイアウト標準仕様**

を定義する。

---

# 関連ドキュメント

```
docs/core/ui/ui_design_system.md
docs/core/GenesisPrediction_UI_Work_Rules.md
```

```

