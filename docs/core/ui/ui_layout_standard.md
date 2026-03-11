# UI Layout Standard
GenesisPrediction v2

Version: 1.2  
Status: Active  
Location: docs/core/ui/

---

# 1. Purpose

この文書は、GenesisPrediction UI における  
**ページ骨格・配置・見た目の標準レイアウト**を定義する。

目的

- 全ページの骨格を固定する
- AIがページごとに勝手なレイアウト変更を行うのを防ぐ
- UI統一を「見た目」ではなく「構造」で維持する
- 長期保守時のレイアウト事故を防ぐ
- Header / Global Status / Hero / Content / Footer の順序を固定する

この文書は **ページ全体のレイアウト標準**を扱う。  
データ依存関係は `ui_data_dependencies.md`、  
UI全体責務は `ui_system.md`、  
設計思想は `ui_design_philosophy.md` を正とする。

---

# 2. Scope

対象ページ

- Home
- Overlay
- Sentiment
- Digest
- Prediction
- Prediction History

これらのページは、同一のレイアウト原則に従う。  
各ページは役割や読むデータが異なっても、  
**骨格は共通**でなければならない。

---

# 3. Core Layout Philosophy

GenesisPrediction UI の最重要原則はこれである。

```

Clarity over decoration
装飾より可読性

```

GenesisPrediction UI はニュースサイトやブログではなく、  
**Research Dashboard / Observation Dashboard** として設計されている。

そのためレイアウトは派手さより

- 状態把握
- 情報階層
- 読みやすさ
- 比較しやすさ
- 壊れにくさ

を優先する。

---

# 4. Standard Page Skeleton

全ページは以下の標準骨格を持つ。

```

#site-header
.container
Global Status
Hero Section
Main Content
Cards / Panels
Timeline / Lists / Detail Sections
#site-footer
/static/common/layout.js

```

---

# 5. Standard Section Order

標準順序

```

1 Header
2 Global Status
3 Hero
4 Primary Summary
5 KPI / Key Metrics
6 Main Content
7 Timeline / Lists / Detail
8 Footer

```

---

# 6. Container Rule

ページ本体は `.container` 内に置く。

原則

- header / footer は共通差し込み
- ページ本文は `.container`
- body直下に大量要素を並べない
- 横幅は app.css の container ルールで統一する

重要原則

```

共通幅は app.css
ページはその中に置く

```

---

# 7. Shared Layout Shell Rule

GenesisPrediction UI の全ページは  
**共通レイアウトシェルを必ず使用する。**

ページごとに独自 header / footer を作ってはならない。

標準構造

```

#site-header
.container
Global Status
Hero
Main Content
#site-footer
/static/common/layout.js

```

---

## Shared Components

共通UIシェルは以下のファイルで構成される。

```

app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js
app/static/app.css

```

---

## Page HTML Responsibility

各ページ HTML の責務は

```

ページ固有コンテンツのみ

```

とする。

つまり

```

Header
Footer
Layout

```

は **共通コンポーネントが管理する。**

---

## Forbidden Implementation

以下は禁止

- ページ内に独自 header を書く
- ページ内に独自 footer を書く
- layout.js を使わない
- 共通 CSS を page HTML で再定義する

---

# 8. Panel Rule

GenesisPrediction UI の基本表示単位は **panel / card** である。

原則

- 主要セクションは panel で包む
- panel の中に card / grid / list を置く
- 画面全体を裸の要素列にしない
- セクションごとの役割を視覚的に分離する

---

# 9. Global Status Rule

Global Status はページ最上部の本文先頭に置く。

Header 直下  
Hero の上

重要原則

- Header の中に埋め込まない
- Hero の下に移動しない
- ページごとに位置を変えない
- **5-card 横並び構造を守る**

標準カード

```

Latest Date
Global Risk
Dominant
Confidence
Snapshots

```

---

# 10. Hero Rule

Hero はページ説明層。

役割

- ページタイトル
- 説明文
- 見方
- metadata

原則

- 長文禁止
- 説明は短く
- 装飾より概要

---

# 11. KPI Layer Rule

Hero の次に置く。

例

Sentiment

```

positive
negative
neutral
mixed
total

```

Prediction

```

risk
confidence
horizon
signal count

```

---

# 12. Main Content Rule

Main Content はページの主目的。

```

Main Content がページ本体
Hero / KPI は補助

```

---

# 13. Timeline / Lists Rule

Main Content の下に配置。

用途

- 履歴
- 詳細
- watchpoints
- article lists

---

# 14. Section Title Rule

各 panel は title を持つ。

例

- Global Status
- Summary
- KPI
- Highlights
- Articles
- Watchpoints
- History Review

---

# 15. Grid Rule

GenesisPrediction UI は grid ベース。

例

Global Status

```

5 columns

```

Hero

```

2 column desktop
1 column mobile

```

History

```

2 column desktop
1 column mobile

```

---

# 16. Height Alignment Rule

横並びカードは高さを揃える。

目的

```

比較しやすさ

```

---

# 17. Reading Flow Rule

```

Global Status
↓
Page Summary
↓
Key Metrics
↓
Content
↓
History

```

---

# 18. Responsive Rule

変更してよい

- 列数
- gap
- padding

禁止

- モバイル専用DOM
- 構造変更
- セクション削除

---

# 19. CSS Responsibility Rule

共通CSS

```

app/static/app.css

```

責務

- container
- panel
- card
- typography
- grid
- nav

ページCSS

```

最小限

```

禁止

- inline style
- JS style manipulation

---

# 20. Base Page Reference

GenesisPrediction UI の **レイアウト基準ページは**

```

index.html

```

とする。

以下のページは **index と完全一致レイアウトを維持する**

```

index.html
overlay.html
sentiment.html
digest.html

```

新しい UI ページを作る場合

```

index.html をコピーして作る

```

これにより

- headerズレ
- fontサイズ差
- padding差
- nav位置ズレ

を防ぐ。

---

# 21. Prediction Page Layout

Prediction 系ページは以下の構造を持つ。

```

Hero
Global Status
Prediction Summary
Metrics
Timeline / Charts
Notes

```

対象

```

prediction.html
prediction_history.html

```

---

# 22. Prediction History Layout

Prediction History ページは以下の情報構造を持つ。

```

Global Status
Prediction Summary
History Timeline
History Charts
History Notes

```

目的

```

prediction drift
risk evolution
confidence change
scenario shift

```

を時系列で観測する。

---

# 23. Screenshot Reference

Prediction History レイアウト例

- Global Status
- Risk drift panel
- Timeline
- Charts
- Notes

このスクリーンショットを **UI基準参考資料**として保存する。

理由

AIは文章より  
**レイアウト画像を優先して理解するため。**

---

# 24. Relationship to Other UI Standards

```

ui_design_philosophy.md
ui_component_catalog.md
ui_layout_standard.md
global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md

```

---

# 25. Forbidden Layout Changes

禁止

- Header 位置変更
- Global Status 移動
- Hero 削除
- KPI順序変更
- layout.js を使わない
- index基準から逸脱する

---

# 26. Definition of Done

ページが完成とみなされる条件

- 共通骨格を持つ
- Header → Global Status → Hero → Content → Footer
- section title 整理
- panel/card 再利用
- first view で理解できる

---

# 27. Version History

v1.0  
Initial layout standard

v1.1  
Add Shared Layout Shell Rule

v1.2  
Add Base Page Reference / Prediction Layout / Screenshot Reference
```
