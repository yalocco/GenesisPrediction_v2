# GenesisPrediction UI Layout Standard

この文書は GenesisPrediction UI のレイアウト構造を定義する。

目的

- UI構造の統一
- レイアウト崩れ防止
- AI作業時の参照基準
- 新規ページ作成時のテンプレート
- 共通レイアウト部品の安全な再利用
- DOM id 衝突の防止


---

# UIアーキテクチャ

GenesisPrediction UI は以下の **3層構造** で管理される。

```text
Theme Layer
Layout Layer
Page Layer
````

構造

```text
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

```text
Header
Hero
Main Content
Panels
Footer
```

例

```text
<header>
hero
panel
grid
panel
</main>
<footer>
```

Header / Footer は `layout.js` が生成する。

---

# Header構造

Header は **layout.js によって自動生成される。**

構造

```text
Topbar
Brand
Navigation
Health Status
```

Navigation

```text
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

```text
Hero Title
Hero Summary
Hero Meta
```

例

```text
GenesisPrediction
Global Situation Overview
as_of 2026-03-12
```

---

# Panel構造

UIの基本単位。

```text
.panel
```

内容

```text
section header
grid
card
list
timeline
```

例

```text
.panel
.section-header
.card
```

---

# Grid構造

レスポンシブ対応の基本構造。

```text
grid-2
grid-3
stack
```

grid-2

```text
2 column
```

grid-3

```text
3 column
```

stack

```text
vertical list
```

---

# KPI / Metric構造

数値表示コンポーネント。

```text
.metric-card
.metric-label
.metric-value
.metric-sub
```

使用例

```text
FX Rate
Sentiment Score
Risk Index
```

---

# Global Status構造

システム状態表示。

```text
.global-status
.status-card
.status-label
.status-value
.status-sub
```

表示例

```text
News
Sentiment
Prediction
FX
System
```

---

# Navigationルール

nav は以下の条件を満たす。

```text
固定高さ
固定padding
hover変化あり
active表示あり
```

nav は `layout.js` が生成する。

---

# Footer構造

Footer は共通。

```text
GenesisPrediction v2
UI is read-only
analysis is SST
```

---

# DOM ID Collision Rule

Header components と page components は
**同じ DOM id を共有してはいけない。**

理由

```text
document.getElementById() は最初の一致要素を返す
重複 id があると更新対象が誤る
header 更新が page 側に当たる、またはその逆が起きる
as_of / ready / status pill の表示不整合が発生する
```

特に以下のような **共通 header 用 id** は予約扱いとする。

```text
pillAsOf
pillReady
pillHealth
pillStatus
```

これらを各ページ本文側で再使用してはいけない。

ページ固有要素は **page prefix 付き id** を使う。

正しい例

```text
overlayAsOf
overlayReady
digestAsOf
digestReady
predictionAsOf
predictionReady
sentimentAsOf
sentimentReady
```

誤った例

```text
pillAsOf
pillReady
```

を header と page 本文の両方で使うこと。

運用ルール

1
共通 id は `layout.js` 専用とする

2
ページ固有 id は page 名 prefix を付ける

3
新規ページ追加時は first render 前に id 重複を確認する

4
共通 script が更新する id と page script が更新する id を分離する

5
as_of / updated / ready / health 系の pill は重複禁止とする

---

# 新規ページ作成ルール

新しいページを作る場合

1
HTMLは content のみ作る

2
Header / Footer は `layout.js` に任せる

3
CSSは `app.css` を使用

4
個別CSSは禁止

5
共通 id を再利用しない

6
ページ固有 pill / status / meta には page prefix を付ける

---

# UI変更ルール

UI変更は必ず

```text
app/static/app.css
```

から行う。

HTML の style 編集は禁止。

ただし、緊急安定化対応として一時的に inline style / page 内 style を使った場合は、
最終的に `app.css` へ統合すること。

---

# as_of / updated / date ルール

日付表示は意味を混在させてはいけない。

基本方針

```text
analysis = SST
digest = presentation
UI = read-only
```

運用ルール

1
Header の as_of は共通レイアウト側で管理する

2
Global Status の updated は analysis 系最新日時を優先する

3
Digest view_model の date を全ページ共通 as_of の基準にしてはいけない

4
page 固有 as_of は page 固有 id で描画する

5
同一ページ内に複数の as_of がある場合は、役割を分けて管理する

---

# 既存ページ

GenesisPrediction UI は現在以下のページを持つ。

```text
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

```text
docs/core/ui/ui_design_system.md
docs/core/GenesisPrediction_UI_Work_Rules.md
```
