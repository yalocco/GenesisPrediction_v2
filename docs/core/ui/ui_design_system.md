# GenesisPrediction UI Design System

この文書は GenesisPrediction UI のデザインシステムを定義する。

目的

- UIデザインの統一
- CSS設計の標準化
- AI作業時の参照仕様
- 新規ページ作成時のデザイン指針


---

# Theme System

GenesisPrediction UI は **Theme System** で管理される。

Core Theme File

```

app/static/app.css

```

このファイルが UI デザインの中心となる。


---

# Theme構造

Theme は以下の要素で構成される。

```

Variables
Typography
Layout
Components
Grid
Utilities

```


---

# Variables

デザイン変数は CSS Variables で管理する。

例

```

--bg
--bg-elevated

--panel-bg
--panel-bg-soft

--border-color
--border-strong

--text-main
--text-muted
--text-dim

--accent
--accent-soft

```

Spacing

```

--space-1
--space-2
--space-3
--space-4
--space-5
--space-6

```

Radius

```

--radius-sm
--radius-md
--radius-lg
--radius-xl

```

Shadow

```

--shadow-sm
--shadow-md
--shadow-lg

```


---

# Typography

基本フォント

```

system-ui
Segoe UI
Roboto
Helvetica
Arial

```

基本スタイル

```

.h1
.hero-title
.section-title
.metric-value
.small
.hint
.mono

```


---

# Layout Components

UIの基本構造

```

container
panel
card
hero
section
footer

```

container

ページ幅管理

panel

UIの基本ブロック

card

panel内のコンテンツ要素


---

# Navigation Components

```

topbar
nav
nav-link
brand
health-line

```

nav-link

```

hover
active

```

を持つ。


---

# Grid System

レスポンシブレイアウトの基本。

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

vertical layout

```


---

# Status Components

システム状態表示。

```

global-status
status-grid
status-card
status-label
status-value
status-sub

```

例

```

News
Sentiment
Prediction
FX
System

```


---

# KPI Components

数値表示コンポーネント。

```

metric-card
metric-label
metric-value
metric-sub

```

用途

```

FX Rate
Sentiment Score
Risk Index

```

---

# Lists / Timeline

記事やイベント表示。

```

timeline
timeline-card
timeline-title
timeline-summary
plain-list

```

用途

```

news
events
signals
scenarios

```


---

# Buttons

```

btn
pill
pillrow

```

UI操作に使用。


---

# Form Components

```

select
input
textarea

```

データ選択・入力。


---

# UI設計原則

GenesisPrediction UI は以下の原則で設計する。


## 1  
Theme First

UI変更は **app.css から行う。**


## 2  
Layout Separation

レイアウトは

```

layout.js

```

が管理する。


## 3  
Content Only HTML

HTMLは

**contentのみ**

を書く。


## 4  
CSS Local禁止

HTML内

```

style

```

は禁止。


---

# UIの役割

GenesisPrediction UI は

```

Observation
Trend
Signal
Scenario
Prediction

```

を可視化するための

**Visualization Layer**

である。


---

# UIの性質

UIは

```

Read Only

```

である。

データは

```

analysis

```

ディレクトリから読み取る。


---

# SST

Single Source of Truth

```

analysis/

```

UIは分析結果を表示するのみ。


---

# 対象ページ

GenesisPrediction UI

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

**Design System 仕様**

を定義する。


---

# 関連ドキュメント

```

docs/core/ui/ui_layout_standard.md
docs/core/GenesisPrediction_UI_Work_Rules.md

```
```
