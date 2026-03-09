# UI Layout Standard

GenesisPrediction v2

Status: Active
Purpose: UIレイアウトの標準構造を固定し、全ページで同じ骨格・同じ判断基準を維持する
Last Updated: 2026-03-09

---

# 0. Purpose

このドキュメントは、GenesisPrediction v2 の UI レイアウト標準を定義する。

目的

- 全ページの骨格を統一する
- 新規ページ追加時に迷わないようにする
- UI改修時に「どこまで変えてよいか」の判断基準を固定する
- デザイン変更で既存ページの一貫性が壊れることを防ぐ
- AIが新しいページを作る時に既存UIと揃った構造を再現できるようにする

GenesisPrediction UI は単発ページの集合ではない。

```text
統一された研究ダッシュボード群
```

として扱う。

---

# 1. Core Principle

UIレイアウトの最重要原則はこれである。

```text
全ページは同じ骨格を持つ
```

見た目を揃える目的は装飾ではない。

目的は

```text
どのページでも迷わず読めること
```

である。

そのため、各ページはページ固有の内容を持っていても、レイアウト骨格は共通とする。

---

# 2. Target Pages

本標準の対象ページは以下である。

```text
app/static/index.html
app/static/overlay.html
app/static/sentiment.html
app/static/digest.html
app/static/prediction.html
app/static/prediction_history.html
```

これらはすべて

```text
共通 header / footer / layout.js
```

を用いる統一UIとして扱う。

---

# 3. Standard Page Skeleton

全ページの基本骨格は以下で固定する。

```text
#site-header
main.page-shell
  .container
    .panel
      Global Status
      Hero Section
      Main Content Sections
#site-footer
/static/common/layout.js
```

順序を崩さないこと。

特に重要なのは以下である。

```text
Header
↓
Global Status
↓
Hero
↓
Main Content
↓
Footer
```

Global Status を Hero より上に置くことで、ユーザーはまず「今の全体状態」を把握し、その後にページ固有の内容へ進める。

---

# 4. Shared Runtime Layout

全主要ページは以下の共通部品を使用する。

```text
app/static/app.css
app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js
```

原則

```text
ページごとに header / footer を独自実装しない
```

理由

- ナビゲーション不一致を防ぐ
- ページ間のブランド差をなくす
- 微修正を全ページへ同時適用しやすくする
- 新しいAIが1ページだけ古いレイアウトを生成する事故を防ぐ

---

# 5. Navigation Standard

主要ナビゲーションは以下で固定する。

```text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

Header では

```text
ブランド
+ 主要ナビゲーション
```

を横並びに配置する。

ルール

- 全ページで同一順序にする
- 同じ文言を使う
- ページごとにリンク順を変えない
- 旧ページだけリンクが欠ける状態を作らない

---

# 6. Container and Panel Standard

ページ本体は以下の二重構造を標準とする。

```text
container
  panel
```

## container

役割

```text
ページ全体の横幅制御
```

ルール

- 読みやすい最大幅を持つ
- 画面端まで情報を広げすぎない
- モバイル時は自然に1列へ落ちる

## panel

役割

```text
1ページ全体を包む主表示面
```

ルール

- ダーク系の統一背景
- 角丸
- 細い境界線
- 過剰な装飾を入れない

panel はページごとに別物を作らず、全ページ共通の視覚基盤とする。

---

# 7. Global Status Standard

Global Status は全主要ページで共通表示とする。

構造

```text
status-shell
  status-grid
    5 status-item
```

標準は

```text
5-card 横並び
```

である。

表示対象の代表例

```text
global risk
sentiment balance
FX regime
article count
last update
```

ルール

- 縦長のテキストダンプにしない
- ページごとに件数を増減させない
- 横並びが崩れた場合はまずCSSまたはページ固有マークアップを疑う
- Prediction / Prediction History でも同じ見え方を維持する

重要原則

```text
Global Status はページ固有情報ではなく全体把握用
```

である。

---

# 8. Hero Section Standard

Global Status の下には必ず Hero Section を置く。

構造

```text
hero
  title
  summary
  meta / pills
```

役割

- このページが何を示すかを短く説明する
- 現在値の要点を先に伝える
- 以降の詳細カードを読む前提を作る

ルール

- 長文説明を入れすぎない
- 1画面目でページの意味が分かるようにする
- KPIカード群の代替にしない
- Hero の見た目はページごとに別系統へ崩さない

---

# 9. Main Content Section Standard

Hero の下はページ固有コンテンツ領域とする。

代表構成

```text
section title
cards / lists / charts / timeline
```

各セクションは以下の考え方で組む。

```text
1 section = 1 purpose
```

例

- Overview
- Metrics
- Articles
- Watchpoints
- History
- Timeline

ルール

- 1セクションに複数目的を詰め込みすぎない
- 見出しを付ける
- セクション間に十分な余白を取る
- 似た情報はカード群で並べる
- 詳細列挙と要約表示を混在させすぎない

---

# 10. Card Standard

情報表示の基本単位は card とする。

構造

```text
card
  title
  body
```

カードの用途

```text
KPI
summary
article
prediction snapshot
history item
watchpoint list
```

ルール

- 全ページで同系統の角丸・境界線・背景トーンを使う
- カードの中にさらに不要なカードを重ねすぎない
- 一覧性を壊すほど装飾しない
- 数値カードと文章カードの役割を分ける

---

# 11. Grid Standard

標準グリッドは以下を再利用する。

```text
hero-grid
kpi-grid
history-grid
status-grid
```

原則

- デスクトップは複数列
- 狭い画面では1列へ自然に落とす
- 無理な固定列数を避ける
- ページごとに独自グリッド名を増やしすぎない

特に KPI は

```text
横並びで比較できること
```

が重要である。

---

# 12. Timeline and List Standard

時系列表示には timeline 系を使う。

構造

```text
timeline-card
  timeline-list
    timeline-row
```

注視点・補助項目・短い列挙には list-stack を使う。

構造

```text
list-stack
  list-row
```

使い分け

## timeline

- 日付
- 変化
- 履歴比較
- ドリフト確認

## list-stack

- watchpoints
- drivers
- alerts
- notes

---

# 13. Prediction Pages Standard

Prediction / Prediction History は、既存4ページと別系統にしない。

守るべき順序

```text
Header
Global Status
Hero
Primary Summary Cards
Detailed Sections
Footer
```

特に以下を守る。

- Prediction だけ独自トップ構造にしない
- Prediction History だけテキスト中心ページにしない
- Global Status を巨大な説明文に置き換えない
- History 本体は時系列比較へ集中させる

Prediction 系も

```text
研究ダッシュボードの1ページ
```

として扱う。

---

# 14. Empty / Loading / No Data Standard

データ欠損時も UI は停止してはならない。

標準状態

```text
loading
empty
unavailable
error-safe fallback
```

ルール

- 何も描けない場合でも panel を崩さない
- セクションごとに空状態を見せる
- JSON 欠損でページ全体を真っ白にしない
- 取得失敗時は短い説明だけ出す
- ダミー数値を捏造しない

重要原則

```text
UI は安全に空であることができる
```

---

# 15. Footer Standard

Footer は全ページ共通とする。

役割

- ページ群としての一体感を保つ
- UIの終端を明確にする
- 個別ページで独自 footer を増やさない

ルール

- 共通 footer を layout.js 経由で入れる
- ページ別の余計な終端情報を追加しない

---

# 16. Spacing and Visual Rhythm

読みやすさのため、余白設計は統一する。

原則

```text
詰め込みすぎない
```

ルール

- Global Status と Hero の間に明確な区切りを持たせる
- Hero と最初のコンテンツ群を近づけすぎない
- セクションごとに一定の縦余白を維持する
- カード内余白を削って情報密度だけを上げない

GenesisPrediction UI は高密度でよいが、窮屈であってはならない。

---

# 17. What Must Not Be Changed Casually

以下は軽い気分で変更してはならない。

```text
Header structure
Navigation order
Global Status location
Hero placement
Panel / Card baseline
Footer insertion model
共通 layout.js 前提
```

これらは UI 全体の骨格であり、1ページだけ変更すると統一性が崩れる。

---

# 18. When Adding a New Page

新しいUIページを追加する場合は以下を守る。

```text
1. 既存 header / footer / layout.js を使う
2. Global Status を置く
3. Hero を置く
4. Main content を card / list / timeline で構成する
5. docs/ui_data_dependencies.md を更新する
6. 必要なら docs/ui_component_catalog.md も更新する
7. 標準から逸脱したらこの文書も更新する
```

---

# 19. Relation to Other Docs

本標準は単独ではなく、以下とセットで使う。

```text
docs/core/ui_design_philosophy.md
docs/core/ui_component_catalog.md
docs/core/GenesisPrediction_UI_Work_Rules.md
docs/active/ui_system.md
docs/active/ui_data_dependencies.md
```

役割分担

## ui_design_philosophy.md

思想

## ui_component_catalog.md

部品定義

## UI_Work_Rules.md

作業手順

## ui_system.md

UI全体責務

## ui_data_dependencies.md

データ依存

## ui_layout_standard.md

ページ骨格の標準

---

# 20. Final Principle

GenesisPrediction UI のレイアウト標準を一言で言うと

```text
同じ骨格で、違う情報を見せる
```

である。

全ページは

```text
研究ダッシュボードとして一貫して見えること
```

を優先する。

派手さより

```text
統一感
可読性
再現性
```

を守ること。

---

END OF DOCUMENT
