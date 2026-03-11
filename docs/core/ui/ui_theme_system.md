# UI Theme System
GenesisPrediction v2

Version: 1.0  
Status: Active  
Location: docs/core/ui/  
Purpose: ページ個別調整をやめ、共通テーマで UI を完全統一するための実装標準を定義する

---

# 1. Purpose

この文書は、GenesisPrediction UI における  
**共通テーマシステム（Theme System）** を定義する。

目的

- ページごとの個別CSS調整を終了する
- UIの見た目をテーマ層へ集約する
- 新規ページが **テーマCSSを読むだけで成立する構造** を作る
- HTML内のstyle記述を最小化し、AI / 人間の実装事故を減らす
- `prediction.html` / `prediction_history.html` を最後に安全にテーマへ載せ替えられるようにする

GenesisPrediction UI の原則は

```text
Clarity over decoration
装飾より可読性
````

であり、テーマシステムはその思想を
**再利用可能な共通見た目** として固定するために存在する。

---

# 2. Scope

対象

```text
app/static/app.css
app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js

app/static/index.html
app/static/overlay.html
app/static/sentiment.html
app/static/digest.html
app/static/prediction.html
app/static/prediction_history.html
```

将来的に必要であれば以下の分割を許可する。

```text
app/static/app.css
app/static/theme.css
app/static/layout.css
app/static/components.css
```

ただし v1 の公式入口は常に

```text
app/static/app.css
```

とする。

---

# 3. Core Principle

UI Theme System の最重要原則はこれである。

```text
見た目の責務を HTML から CSS へ戻す
```

つまり

* HTML はページ固有コンテンツを書く
* 共通見た目はテーマCSSが持つ
* ページごとの inline style / page-local style を増やさない
* 新規ページでデザインを作り込まない

重要原則

```text
新規ページはテーマを読むだけで成立する
```

---

# 4. Relationship to Existing UI Standards

UI Theme System は既存UI標準の上に成立する。

関係

```text
ui_design_philosophy.md
    = UI思想

ui_component_catalog.md
    = 再利用部品辞書

ui_layout_standard.md
    = ページ骨格標準

global_status_*.md
    = 最重要共通コンポーネント標準

ui_theme_system.md
    = 共通見た目の実装層
```

重要:

```text
Theme System は layout standard を置き換えない
Theme System は component catalog を置き換えない
Theme System はそれらを実装しやすくするための CSS 標準である
```

---

# 5. Theme Architecture

GenesisPrediction UI Theme System は
次の4層構造で考える。

```text
Layer 1
Design Tokens

Layer 2
Layout Theme

Layer 3
Component Theme

Layer 4
Page Content
```

意味

## Layer 1 — Design Tokens

色、余白、角丸、影、文字サイズなどの共通変数

## Layer 2 — Layout Theme

container, panel, grid, spacing, section order を支える共通レイアウト見た目

## Layer 3 — Component Theme

hero, global status, card, list, timeline, badge などの部品見た目

## Layer 4 — Page Content

各ページ固有のデータ表示内容
ただし見た目はテーマ層を再利用する

---

# 6. CSS File Responsibility

v1 では以下の責務を採用する。

## 6.1 app.css

`app.css` は **テーマシステムの公式入口** とする。

責務

* CSS Variables
* reset / base
* container
* panel
* card
* typography
* spacing
* nav
* hero
* global status
* section header
* common grid
* list / timeline
* state styles
* responsive

原則

```text
まず app.css を正とする
```

---

## 6.2 theme.css（任意）

任意導入。
導入する場合は

* color tokens
* typography tokens
* spacing tokens
* radius / shadow tokens

を持つ。

---

## 6.3 layout.css（任意）

任意導入。
導入する場合は

* container
* page shell
* grid
* section spacing
* responsive layout

を持つ。

---

## 6.4 components.css（任意）

任意導入。
導入する場合は

* hero
* global status
* cards
* pills
* badges
* list-stack
* timeline
* sparkline

を持つ。

---

# 7. Recommended Rollout Strategy

Theme System は一気に全ページを書き換えるより、
次の順序で載せ替える。

```text
Step 1
app.css の責務を固定

Step 2
共通コンポーネント class を固定

Step 3
Prediction をテーマへ載せ替え

Step 4
Prediction History をテーマへ載せ替え

Step 5
必要なら他ページを同一 class へ収束
```

理由

* index は現行の基準ページ
* prediction / prediction_history は最後の統一対象
* 最も崩れやすいページを後ろに回すことで事故を減らす

---

# 8. Theme Tokens Standard

共通見た目は CSS Variables で制御する。

最低限必要な token 群

```text
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
--success
--warn
--danger

--radius-sm
--radius-md
--radius-lg
--radius-xl

--shadow-sm
--shadow-md
--shadow-lg

--space-1
--space-2
--space-3
--space-4
--space-5
--space-6

--container-max
--panel-gap
--card-gap
--section-gap
```

重要原則

```text
色・余白・角丸・影を個別ページで直書きしない
```

---

# 9. Shared Layout Theme Rules

全ページ共通で統一する見た目は次の通り。

## 9.1 Container

* すべて `.container`
* 最大幅は共通 token で固定
* ページごとに width を変えない

## 9.2 Panel

* 主セクションは panel で包む
* panel 外に裸の大量要素を置かない
* 背景、境界線、角丸、padding は共通

## 9.3 Card

* 情報ブロックは card を再利用
* 角丸・border・背景・shadow を統一
* ページ独自カードを増やさない

## 9.4 Grid

* grid ルールは app.css で統一
* 同じ役割の grid は同じ class を使う
* prediction だけ別 grid、history だけ別 grid、の乱立を禁止する

---

# 10. Shared Component Theme Rules

## 10.1 Hero

Hero は全ページ共通テーマを持つ。

構成

```text
.hero
.hero__body
.hero__title
.hero__summary
.hero__meta
.hero__pill
```

役割

* タイトル
* 要約
* メタ情報

禁止

* ページごとの hero 専用見た目
* Hero を毎回作り直すこと

---

## 10.2 Global Status

Global Status は最優先共通テーマ対象である。

構成

```text
.global-status-panel
.global-status
.status-card
.status-label
.status-value
.status-sub
```

固定事項

* 5カード構造
* 共通DOM
* 共通CSS
* ページ別 override 禁止

---

## 10.3 Section Header

各主要セクションは共通の section header を持つ。

構成

```text
.section-header
.section-title
.section-subtitle
.section-actions
```

目的

* 各ページの section title の見た目統一
* 「Summary」「KPI」「Highlights」「History Review」などのばらつきを抑える

---

## 10.4 Card / Panel / Grid Spacing

余白ルールは共通化する。

統一対象

* panel padding
* panel gap
* card padding
* card title margin
* grid gap
* section vertical spacing

禁止

```text
margin-top: 37px
padding: 19px 21px
```

のような場当たり的調整

---

## 10.5 Lists / Timeline

Prediction / Prediction History で使う list / timeline も共通テーマ対象とする。

構成

```text
.list-stack
.list-row
.timeline-card
.timeline-list
.timeline-row
```

---

# 11. Page HTML Responsibility

各ページHTMLの責務は

```text
ページ固有データの配置だけ
```

とする。

ページ側でやってよいこと

* JSON を読む
* 値を差し込む
* テーマclassを使って並べる

ページ側でやってはいけないこと

* 共通見た目の再定義
* 独自の大量CSS
* 色や余白の個別調整
* 共通部品の別名実装

---

# 12. New Page Rule

新規ページは次の原則で作る。

```text
1. layout.js を使う
2. app.css を読む
3. 既存 class のみで骨格を組む
4. ページ専用 CSS は最小限
5. 共通部品を再実装しない
```

新規ページ作成時の推奨順序

```text
Global Status
Hero
Primary Panel
Cards / Detail Sections
Lists / History
```

重要原則

```text
新規ページでデザインを発明しない
```

---

# 13. Prediction Page Theme Migration Rule

`prediction.html` をテーマへ載せ替える時の原則

* Global Status は共通 class 化する
* Hero を共通 hero class 化する
* summary / confidence / risk / scenario の表示カードを共通 card 化する
* watchpoints / drivers / invalidation / implications を list-stack 化する
* prediction 専用の装飾CSSを極小化する

目的

```text
Prediction を「特別ページ」ではなく
共通テーマ上の1ページに戻す
```

---

# 14. Prediction History Theme Migration Rule

`prediction_history.html` をテーマへ載せ替える時の原則

* 上部 Global Status は prediction と同一構造
* Hero は prediction と同一テーマ
* window selector / summary / drift cards は共通 card / panel を使う
* history rows は timeline / list 系コンポーネントへ寄せる
* 履歴専用の場当たり CSS を作らない

目的

```text
Prediction History を「例外UI」にしない
```

---

# 15. Theme Naming Rules

class 命名は役割ベースで統一する。

推奨

```text
.panel
.card
.hero
.section-header
.kpi-grid
.history-grid
.list-stack
.timeline-card
```

禁止

```text
.prediction-special-box
.history-box-2
.new-panel-final
```

のような一回限り命名

重要原則

```text
名前は見た目ではなく役割で付ける
```

---

# 16. CSS Override Rules

禁止

* inline style
* JS による style 直接変更
* ページ末尾に大量 style を追記
* 同じ class をページごとに上書き
* `!important` 乱用

許可

* app.css 内での正規定義
* 必要最小限の page-local CSS
* state attribute による見た目分岐

---

# 17. Responsive Rule

Theme System は responsive を app.css 側で吸収する。

許可される調整

* column 数
* gap
* padding
* font size の段階調整

禁止

* モバイル専用 DOM
* ページごとの独自 breakpoints 乱立
* structure 自体の変更

---

# 18. Migration Done Definition

Theme 化完了とみなす条件

## app.css / theme layer

* 共通 token が存在する
* panel / card / hero / global status / section header が共通化されている
* 共通 spacing rule が存在する
* prediction / prediction_history 用の見た目がテーマclassへ収束している

## page HTML

* 独自 header / footer を持たない
* 大量 inline style が無い
* page-local style が最小限
* 既存 theme class のみで大半を組める

## operation

* 新規ページを theme class だけで組める
* 以後の UI 修正が「ページ個別微調整」ではなく「テーマ調整」になる

---

# 19. Final Principle

GenesisPrediction UI Theme System の設計原則を一言で言うと

```text
Page-specific tuning must end.
Theme-driven consistency must become the default.
```

日本語では

```text
ページ個別調整を終わらせ、
テーマ駆動の統一を標準にする
```

である。

---

# 20. Final Summary

GenesisPrediction UI Theme System は

```text
Design Tokens
↓
Layout Theme
↓
Component Theme
↓
Page Content
```

の4層で構成する。

公式入口は

```text
app/static/app.css
```

とし、必要に応じて

```text
theme.css
layout.css
components.css
```

へ分割してよい。

ただし重要なのは分割そのものではない。

重要なのは

```text
新規ページはテーマCSSを読むだけで成立する
```

状態を作ることである。

そのために

* Global Status
* Hero
* Section Header
* Card / Panel / Grid Spacing
* Prediction
* Prediction History

を共通テーマへ収束させる。

GenesisPrediction UI は今後

```text
個別調整型UI
```

ではなく

```text
共通テーマ型UI
```

として運用する。

---

END OF DOCUMENT

```
