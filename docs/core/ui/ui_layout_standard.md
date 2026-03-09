# UI Layout Standard
GenesisPrediction v2

Version: 1.0  
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

```text
Clarity over decoration
装飾より可読性
````

GenesisPrediction UI はニュースサイトやブログではなく、
**Research Dashboard / Observation Dashboard** として設計されている。
そのため、レイアウトは派手さより

* 状態把握
* 情報階層
* 読みやすさ
* 比較しやすさ
* 壊れにくさ

を優先する。 

---

# 4. Standard Page Skeleton

全ページは以下の標準骨格を持つ。

```text
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

UI Component Catalog における標準ページ構造も
**Header → Global Status → Hero → Content Cards → Timeline / Lists → Footer** を前提としている。 

---

# 5. Standard Section Order

標準順序は次の通り。

```text
1. Header
2. Global Status
3. Hero
4. Primary Summary / Overview
5. KPI / Key Metrics
6. Main Content
7. Timeline / Lists / Detail Blocks
8. Footer
```

順序の意味

## 1. Header

ブランド・共通ナビゲーション・ページ間移動

## 2. Global Status

ページ冒頭の状況把握
全ページ共通の 5-card overview

## 3. Hero

そのページの意味・要約・読み方

## 4. Primary Summary / Overview

ページの一番重要な一段目
「何を見るページか」をすぐ理解させる

## 5. KPI / Key Metrics

数値の概観
件数・分類・状態を短時間で読むための層

## 6. Main Content

そのページの本体表示

## 7. Timeline / Lists / Detail Blocks

比較、履歴、詳細、レビュー

## 8. Footer

終端統一・ブランド表示・補助導線

---

# 6. Container Rule

ページ本体は `.container` 内に置く。

原則

* header / footer は共通差し込み
* ページ本文は `.container`
* body直下に大量要素を並べない
* 横幅は app.css の container ルールで統一する

重要原則

```text
共通幅は app.css
ページはその中に置く
```

これは UI System が定義する
`#site-header` / `.container` / `#site-footer` の共通骨格と一致させる。 

---

# 7. Panel Rule

GenesisPrediction UI の基本表示単位は **panel / card** である。
新しいページは既存の panel / card を再利用する。

原則

* 主要セクションは panel で包む
* panel の中に card / grid / list を置く
* 画面全体を裸の要素列にしない
* セクションごとの役割を視覚的に分離する

---

# 8. Global Status Rule

Global Status はページ最上部の本文先頭に置く。
Header の直下、Hero の上とする。
Global Status は全ページ共通の最重要コンポーネントであり、
5カード固定構造を守る。

重要原則

* Header の中に埋め込まない
* Hero の下に移動しない
* ページごとに位置を変えない
* 5-card 横並び構造を守る

---

# 9. Hero Rule

Hero はページの説明層である。
UI Component Catalog でも、Hero は
**page explanation / current summary / prediction overview** に使うと定義されている。 

Hero の役割

* ページタイトル
* 短い説明文
* そのページの見方
* 必要なら metadata pills

Hero の原則

* 長文禁止
* 説明は短く
* 見出しと説明を分離
* 装飾より概要把握を優先

---

# 10. KPI / Metric Layer Rule

KPI は Hero の次、Main Content の前に置く。
KPI 層は「概要の数値化」であり、
ページ本体の完全代替ではない。

原則

* 重要数値のみ
* 4〜6個程度まで
* 順位付けや補足は本文で行う
* KPI で本文を置き換えない

ページ例

## Sentiment

positive / negative / neutral / mixed / total

## Digest

articles / risk / net / score など

## Prediction

overall risk / confidence / horizon / signal count など

---

# 11. Main Content Rule

Main Content はページの主目的を果たす領域である。
ページごとの責務は `ui_system.md` を正とする。 

例

## Home

全体状況の軽量サマリー

## Overlay

FX overlay image と decision 表示

## Sentiment

per-article sentiment と trend

## Digest

summary / highlights / articles

## Prediction

latest prediction snapshot

## Prediction History

history snapshot の review / drift 表示

重要原則

```text
Main Content がページの本体
Hero や KPI は補助
```

---

# 12. Timeline / Lists Rule

タイムライン・リスト・詳細ブロックは
Main Content の下に置く。

役割

* 履歴表示
* 比較表示
* watchpoints
* review notes
* article lists
* detail blocks

UI Component Catalog では `timeline-card` / `timeline-row` / `list-stack` / `list-row` を再利用する。 

原則

* 本文より下
* 補足や履歴は後段
* first view を情報過多にしない

---

# 13. Section Title Rule

各主要 panel は section title を持つ。

原則

* 見出し無しの大きい箱を作らない
* section title は短く
* Hero の見出しと section title の役割を混ぜない
* 同じ階層の見出しサイズは揃える

例

* Global Status
* Summary
* KPI
* Highlights
* Articles
* Watchpoints
* History Review

---

# 14. Grid Rule

GenesisPrediction UI は grid ベースで整える。
カードやサマリーを手作業のバラバラ配置で置かない。

推奨 grid

## Global Status

5列固定
詳細は `global_status_css_standard.md` を正とする。 

## KPI Grid

4列前後を基本とする
狭幅では app.css で段組み変更してよい

## Hero Grid

2列 desktop / 1列 mobile を標準とする
UI Component Catalog の `hero-grid` に従う。 

## History Grid

2列 desktop / 1列 mobile を標準とする
UI Component Catalog の `history-grid` に従う。 

---

# 15. Height Alignment Rule

横並びにするカード群は、可能な範囲で高さを揃える。

対象例

* Global Status cards
* KPI cards
* Summary / Highlights の並列ブロック
* Prediction detail cards
* History review cards

原則

* 同列の主要情報カードは高さを揃える
* ただし長文を無理に詰め込まない
* 高さ合わせのために情報を削らない
* 高さ合わせより可読性を優先する

重要原則

```text
揃えるのは見た目のためではなく
比較しやすさのため
```

---

# 16. Reading Flow Rule

ページは上から下へ読むことで
**全体 → 要約 → 数値 → 本体 → 詳細 / 履歴**
の流れになるよう設計する。
これは UI Design Philosophy の
**Information Hierarchy** と一致する。 

つまり

```text
Global Status
↓
Page Summary
↓
Key Metrics
↓
Content Details
↓
Historical Context
```

を守る。

---

# 17. Page-Specific Layout Notes

## Home

* 軽量 overview を優先
* 詳細分析を詰め込みすぎない
* 各専門ページへの導線を持つ

## Overlay

* Hero の下に pair / decision overview
* 主要画像は視認しやすい幅で配置
* 画像と decision を分離しすぎない

## Sentiment

* KPI → trend → article list の順を優先
* 記事一覧は詳細層に置く

## Digest

* Summary → KPI → Highlights → Articles
* Highlights と Articles の責務を混ぜない

## Prediction

* Prediction の本体を早く読める位置に置く
* confidence / scenario / watchpoints を分離する

## Prediction History

* 履歴比較を主役にする
* latest prediction を history の代用にしない
* drift / shift / review を後段で整理する

これらは UI System と UI Data Dependencies の責務定義に沿う。

---

# 18. Responsive Rule

レスポンシブでは **列数だけ** を変えてよい。
構造そのものをページ別に変えてはならない。
この方針は Global Status 標準でも明記されている。

許可

* 5列 → 3列 → 2列
* 2列 → 1列
* gap / padding の縮小

禁止

* モバイルだけ別DOM
* モバイルだけ別順序
* スマホだけ card 数変更
* セクションの存在有無をページ別に変えること

---

# 19. CSS Responsibility Rule

ページ骨格に関わる共通スタイルは
`app/static/app.css` に置く。
UI System でも、共通にすべき見た目は app.css に置くと定義されている。 

app.css の責務

* container
* panel
* card
* common spacing
* common grid
* typography baseline
* nav pill
* shared status / hero / list appearance

ページ個別 CSS の責務

* 本当にそのページ固有の微調整のみ

禁止

* 共通レイアウトを page-specific CSS で上書き
* inline style
* JS による style 操作

---

# 20. Relationship to Other UI Standards

UI標準文書の関係は次の通り。

## ui_design_philosophy.md

思想
何を優先するか

## ui_component_catalog.md

部品
何を再利用するか

## ui_layout_standard.md

骨格
どう並べるか

## global_status_component_standard.md

Global Status の思想と固定構造

## global_status_html_standard.md

Global Status の DOM / JS 実装標準

## global_status_css_standard.md

Global Status の CSS 標準

この分離により

```text
思想
部品
骨格
個別コンポーネント
```

を混ぜずに管理できる。

---

# 21. Forbidden Layout Changes

禁止事項

* Header の位置変更
* Global Status の位置変更
* Hero の削除やページ別順序変更
* KPI を本文の下へ移すなどの勝手な再配置
* ページごとに骨格順序を変える
* 同じ役割なのに別構造を新設する
* 本体と補助の順序を逆転させる
* layout.js / app.css の責務を page HTML に持ち込む

重要原則

```text
新しい見た目のために
既存の理解しやすさを壊さない
```

これは UI Design Philosophy の
**Stability Over Novelty** に対応する。 

---

# 22. Definition of Done

ページレイアウトが標準適合とみなせる条件

* 全対象ページが共通骨格を持つ
* Header / Global Status / Hero / Main Content / Footer の順が揃っている
* section title が整理されている
* panel / card / list / timeline が既存部品で統一されている
* ページ固有内容だけが差になる
* page-specific override が最小限
* first view で「何のページか」がわかる
* 上から読むだけで全体 → 詳細へ入れる

---

# 23. Version History

v1.0
Initial layout standard for GenesisPrediction UI

```
