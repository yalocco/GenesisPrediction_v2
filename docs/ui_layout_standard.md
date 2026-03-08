# UI Layout Standard
GenesisPrediction v2

Status: Active
Purpose: GenesisPrediction UI の標準レイアウト構造を定義する
Last Updated: 2026-03-08

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

UI標準レイアウト

を定義する。

目的

- UI構造をページ間で統一する
- 新規ページ追加時の迷いをなくす
- 表示調整を局所対応ではなく構造対応にする
- Prediction / History 系を含めて共通骨格を持たせる

GenesisPrediction の UI は
単なるページ集合ではなく、

統一されたダッシュボード群

として扱う。

---

# 1. Core Layout Model

GenesisPrediction UI の基本構造は以下とする。

```text
topbar
↓
container
↓
dashboard panel
  ├ left panel
  └ right panel
↓
content section
↓
footer
````

この構造を
GenesisPrediction UI の標準テンプレートとする。

---

# 2. Three-Layer Principle

UI設計の中心原則は以下の三層である。

```text
topbar
container
card
```

---

## 2.1 Topbar

役割

```text
全ページ共通ナビゲーション
```

含むもの

```text
ブランド
主要ページリンク
active表示
```

原則

```text
全ページ共通
```

Topbar は個別ページごとに持たず、
共通部品として管理する。

---

## 2.2 Container

役割

```text
ページ固有コンテンツ領域
```

原則

```text
幅・余白ルールだけ共通
中身はページごとに自由
```

Container そのものは共通部品化しない。

理由

* 各ページの構造が異なる
* index / overlay / sentiment / digest / prediction / history で役割が違う
* 中身まで共通化すると例外処理が増える

---

## 2.3 Card

役割

```text
情報を読む最小単位
```

例

```text
summary card
risk card
health card
chart card
article card
watchpoint card
prediction card
```

原則

```text
見た目は共通
中身は自由
```

統一対象

* 角丸
* border
* glass背景
* shadow
* padding
* 見出しスタイル

---

# 3. Standard Page Structure

各ページの標準構造は以下とする。

```html
<body>

<div id="site-header"></div>

<div class="container">

  <section class="dashboard-layout">
    <section class="left-panel">
      ...
    </section>

    <section class="right-panel">
      ...
    </section>
  </section>

  <section class="content-section">
    ...
  </section>

</div>

<div id="site-footer"></div>

<script src="/static/common/layout.js"></script>

</body>
```

---

# 4. Dashboard Layout Rule

ダッシュボード型ページは以下を基本とする。

```text
Left Panel  = controls / KPI / source / debug / how it works
Right Panel = charts / trends / visual status
Bottom      = articles / lists / tables / details
```

これにより

```text
左 = 操作・説明
右 = 結果・可視化
下 = 詳細本文
```

という自然な視線導線を作る。

---

# 5. Topbar Standard

Topbar の標準項目は以下。

```text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

役割

```text
GenesisPrediction の主要画面へ即移動する
```

表示ルール

* 現在ページのみ active
* 並び順は固定
* 文言は省略しない
* History は `Prediction History` と明記する

---

# 6. Common Fragment Policy

共通部品は以下を使用する。

```text
app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js
```

---

## 6.1 header.html

役割

```text
全ページ共通の topbar
```

---

## 6.2 footer.html

役割

```text
全ページ共通の footer
```

---

## 6.3 layout.js

役割

```text
header / footer 読み込み
active 判定
共通レイアウト初期化
```

これにより
各ページは共通部品を読み込むだけでよい。

---

# 7. What to Commonize

共通化するもの

```text
topbar
footer
container width
container outer spacing
card appearance
button appearance
nav appearance
active style
```

---

# 8. What Not to Commonize

共通化しないもの

```text
container内部構造
ページ固有grid
チャート構造
記事一覧構造
表構造
データ依存ロジック
```

理由

GenesisPrediction の各画面は
同じ骨格を持ちながらも
役割が異なるため。

---

# 9. Sentiment Page as Baseline

現在の UI 基準ページは

```text
sentiment.html
```

である。

理由

* 背景が安定している
* topbar / glass / card の統一感がある
* 情報量が多く、ダッシュボード型UIの基準に向いている

ただし、
Sentiment をそのままコピーするのではなく

Sentiment を抽象化した構造

を標準とする。

---

# 10. Standard Layout Diagram

GenesisPrediction UI 標準図

```text
┌──────────────────────────────────────────────┐
│ Topbar                                       │
│ Brand / Home / Overlay / Sentiment / Digest  │
│ / Prediction / Prediction History            │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Container                                    │
│                                              │
│  ┌────────────────┬──────────────────────┐   │
│  │ Left Panel     │ Right Panel          │   │
│  │                │                      │   │
│  │ Controls       │ Charts               │   │
│  │ KPI            │ Trend                │   │
│  │ Source         │ Visual Status        │   │
│  │ Debug          │                      │   │
│  │ How it works   │                      │   │
│  └────────────────┴──────────────────────┘   │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Content Section                        │  │
│  │ Articles / Tables / Detailed Data      │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Footer                                       │
└──────────────────────────────────────────────┘
```

---

# 11. Page Mapping

各ページへの適用イメージ

---

## 11.1 Home

```text
Left Panel
- summary
- health
- quick links

Right Panel
- key visuals
- daily status

Bottom
- latest events
```

---

## 11.2 Overlay

```text
Left Panel
- pair selector
- decision summary
- source info

Right Panel
- overlay image
- trend / dashboard visuals

Bottom
- notes / related data
```

---

## 11.3 Sentiment

```text
Left Panel
- controls
- KPI
- source
- debug
- how it works

Right Panel
- risk trend
- positive trend
- uncertainty trend

Bottom
- articles
```

---

## 11.4 Digest

```text
Left Panel
- summary
- KPI
- filter / sort

Right Panel
- highlights
- top risk cards

Bottom
- article cards
```

---

## 11.5 Prediction

```text
Left Panel
- prediction summary
- confidence
- dominant scenario

Right Panel
- probability visuals
- scenario chart

Bottom
- drivers / invalidation / implications
```

---

## 11.6 Prediction History

```text
Left Panel
- current vs previous
- persistent watchpoints
- drift summary

Right Panel
- risk timeline
- confidence trend
- worst-case drift

Bottom
- timeline / review notes
```

---

# 12. UX Principle

GenesisPrediction UI の UX 原則

## Principle 1

```text
左で操作し
右で理解し
下で読む
```

---

## Principle 2

```text
情報の重さを下へ流す
```

軽い情報は上、
重い情報は下へ置く。

---

## Principle 3

```text
説明は圧縮する
```

How it works や source/debug は
画面を圧迫しない形に整理する。

---

## Principle 4

```text
まず全体像
次に可視化
最後に詳細
```

---

# 13. Height Balance Rule

左右2カラム構造では
極端な高さ不一致を避ける。

原則

```text
left panel と right panel は
同じ段として読める高さバランスに寄せる
```

完全一致までは要求しないが、
Articles や下段コンテンツが不必要に下へ押し出される配置は避ける。

---

# 14. How It Works Rule

How it works は
縦長の説明領域ではなく

圧縮された説明カード群

として扱うのが望ましい。

推奨構造

```text
step 1
step 2
step 3
step 4
```

を横並び、または2x2で配置する。

目的

* 縦スペース節約
* Articles を上へ持ち上げる
* 説明は維持しつつ情報密度を上げる

---

# 15. Content Section Rule

Content Section は
ページの本体詳細を置く場所である。

例

```text
articles
tables
detailed cards
raw detail
review lists
```

原則

```text
dashboard の下に置く
```

理由

まず上部で状況を理解し、
その後に詳細へ進むため。

---

# 16. Design Stability Rule

UI調整は局所対応ではなく、
この標準レイアウトに沿って行う。

つまり

```text
1ページだけ綺麗
```

ではなく

```text
GenesisPrediction 全体で揃う
```

ことを目指す。

---

# 17. Relation to Existing Rules

このドキュメントは以下と整合する。

* `docs/working_agreement.md`
* `docs/gui_phase2_working_rules.md`
* `docs/ui_system.md`
* `docs/ui_data_dependencies.md`

特に重要な原則

```text
UI = read-only
```

は不変である。

このレイアウト標準は
表示構造の統一であり、
分析ロジックの追加ではない。

---

# 18. Final Principle

GenesisPrediction UI は

```text
見た目を揃えるためのUI
```

ではなく

```text
理解しやすく
壊れにくく
増築しやすいUI
```

でなければならない。

そのため、
標準構造は

```text
topbar
container
card
```

を中心とし、

```text
left panel
right panel
content section
```

で展開する。

これを
GenesisPrediction UI Standard
とする。

---

END OF DOCUMENT

````
