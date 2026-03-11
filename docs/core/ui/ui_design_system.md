# UI Design System
GenesisPrediction v2

Status: Core  
Location: docs/core/ui/  
Purpose: Define the complete UI design system used by GenesisPrediction.

---

# 1. Purpose

この文書は

**GenesisPrediction UI の設計システム全体を定義する。**

目的

- UI設計の全体構造を1枚で示す
- UI関連ドキュメントの役割を整理する
- AI / 開発者がUIを理解する入口を提供する
- UI設計の長期一貫性を維持する

GenesisPrediction UI は

```

Research Dashboard
Observation Dashboard

```

として設計されている。

---

# 2. UI Design System Layers

GenesisPrediction UI は  
次の **4層構造**で設計されている。

```

Layer 1
Design Philosophy

Layer 2
Component Catalog

Layer 3
Layout Standard

Layer 4
Component Standards

```

それぞれの役割は次の通り。

| Layer | Document | Role |
|-----|-----|-----|
| Philosophy | ui_design_philosophy.md | UI思想 |
| Components | ui_component_catalog.md | UI部品 |
| Layout | ui_layout_standard.md | ページ骨格 |
| Standards | global_status_* | コンポーネント仕様 |

---

# 3. Core Design Principle

GenesisPrediction UI の最重要原則

```

Clarity over decoration
装飾より可読性

```

目的は

```

世界の状況を理解すること
危険信号を早く見つけること
判断を助けること

```

である。

UIは派手さではなく

- 可読性
- 情報密度
- 状態把握

を優先する。

---

# 4. Dashboard Concept

GenesisPrediction UI は

```

ニュースサイト
ブログ
SNS

```

ではない。

これは

```

Observation Dashboard
Research Dashboard

```

である。

そのため

- 高情報密度
- 状態把握優先
- 落ち着いたダークテーマ

を採用する。

---

# 5. Standard Page Structure

すべてのページは  
以下の **共通骨格**を持つ。

```

Header
Global Status
Hero
Primary Summary
KPI Layer
Main Content
History / Lists
Footer

```

この構造は  
**すべてのページで固定される。**

対象ページ

```

Home
Overlay
Sentiment
Digest
Prediction
Prediction History

```

---

# 6. Shared Layout System

GenesisPrediction UI は  
**共通レイアウトシェル**を使用する。

共通ファイル

```

app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js
app/static/app.css

```

各ページ HTML の責務

```

ページ固有コンテンツのみ

```

禁止

```

独自 header 実装
独自 footer 実装
layout.js 不使用

```

---

# 7. Core UI Components

UIは再利用コンポーネントで構成される。

主要コンポーネント

```

panel
card
hero
status-shell
timeline
list-stack
sparkline

```

新しいページは  
必ず既存コンポーネントを再利用する。

---

# 8. Information Hierarchy

UIは次の情報階層を持つ。

```

Global Status
↓
Page Summary
↓
Key Metrics
↓
Main Content
↓
Historical Context

```

この順序は

```

全体理解 → 詳細理解

```

を可能にする。

---

# 9. Grid System

GenesisPrediction UI は  
**grid layout** を基本とする。

代表例

Global Status

```

5 columns

```

Hero

```

2 columns desktop
1 column mobile

```

History Cards

```

2 columns desktop
1 column mobile

```

---

# 10. Reusability Principle

UI設計では

```

Reuse > Reinvent

```

を守る。

新しい構造を作る前に  
既存コンポーネントを確認する。

---

# 11. Error Tolerance

UIは壊れない設計にする。

想定問題

```

JSON欠損
API停止
画像404
データ遅延

```

対策

```

fallback
placeholder
safe empty state

```

---

# 12. Performance Philosophy

GenesisPrediction UI は

```

軽量
高速
シンプル

```

を優先する。

そのため

```

重いフレームワークを使わない
不要なJavaScriptを避ける
静的HTML中心

```

を維持する。

---

# 13. Long-Term Maintainability

GenesisPrediction は

```

10年以上続く研究プロジェクト

```

を想定している。

そのため UI は

```

シンプル
理解しやすい
修正しやすい

```

設計である必要がある。

---

# 14. Relationship with Other UI Documents

UI設計は次の文書群で構成される。

## Philosophy

```

ui_design_philosophy.md

```

---

## Components

```

ui_component_catalog.md

```

---

## Layout

```

ui_layout_standard.md

```

---

## Component Standards

```

global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
global_status_data_mapping.md

```

---

# 15. Design Goal

GenesisPrediction UI の最終目的

```

世界の状況を理解する
危険信号を早く見つける
判断を助ける

```

UIは

```

装飾

```

ではなく

```

理解のためのツール

```

である。

---

# End
```
