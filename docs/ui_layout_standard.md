# UI Layout Standard
GenesisPrediction v2

Version: 1.1
Status: Active
Purpose: GenesisPrediction UI の標準レイアウト構造と共通実装ルールを固定する
Last Updated: 2026-03-08

---

# 0. Purpose

このドキュメントは、GenesisPrediction v2 の UI 標準レイアウトを定義する。

目的:

- ページ間の見た目と構造を統一する
- 新規ページ追加時の迷いをなくす
- 表示調整を場当たり対応ではなく構造対応にする
- Prediction / Prediction History を含めた共通骨格を固定する
- AI と人間の双方が、同じ前提で UI を保守できるようにする

GenesisPrediction の UI は、単なる HTML 群ではなく、

```text
統一されたダッシュボード群
```

として扱う。

---

# 1. Core Principle

GenesisPrediction UI の基本原則は以下とする。

```text
共通フレームは固定
ページ本文は用途ごとに分岐
分析ロジックは UI に持ち込まない
UI は read-only 表示層とする
```

つまり:

```text
analysis = Single Source of Truth
UI = analysis / data を読む表示層
```

UI が行ってよいのは以下のみ:

- 読み込み
- 表示整形
- 空値時の fallback 表示
- レイアウト切り替え
- ソートや絞り込みなどの軽い表示操作

UI が持ってはいけないもの:

- 分析値の再計算
- リスク判定の再決定
- 正式データの生成責務

---

# 2. Standard Frame

全主要ページは以下の共通フレームを前提とする。

```text
header
↓
page container
↓
page title / page lead
↓
global status
↓
page-specific sections
↓
footer
```

これを GenesisPrediction UI の標準テンプレートとする。

---

# 3. Common Runtime Parts

主要ページが共通で使う部品は以下。

```text
app/static/app.css
app/static/common/header.html
app/static/common/footer.html
app/static/common/layout.js
```

補足:

- `app.css` は共通見た目の単一ソースとする
- `header.html` は共通ナビゲーションを持つ
- `footer.html` は共通フッタを持つ
- `layout.js` は header / footer の読込と active 表示の初期化を担う

個別ページで独自 topbar を再実装しない。

---

# 4. Standard DOM Structure

各ページの標準構造は以下を基準とする。

```html
<body>
  <div id="site-header"></div>

  <main class="page container">
    <section class="page-hero">
      <h1>Page Title</h1>
      <p class="page-lead">Page description...</p>
    </section>

    <section class="section global-status-section">
      ...
    </section>

    <section class="section">
      ...
    </section>
  </main>

  <div id="site-footer"></div>

  <script src="/static/common/layout.js"></script>
</body>
```

重要:

- `#site-header` と `#site-footer` を使う
- 本文は `page container` 系の共通余白に合わせる
- 共通構造を崩す独自 topbar / footer は作らない
- ヘッダリンク列は中央、Ready / Health / as_of pill 群は右寄せを維持する

---

# 5. Topbar Standard

共通ヘッダで扱う主要ナビは以下。

```text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

ルール:

- 並び順は固定
- 文言は省略しない
- 現在ページのみ active 表示
- ブランド表示は左固定
- ナビボタン列は中央配置
- 状態 pill 群は右配置

これにより、全ページで同じ視線導線を維持する。

---

# 6. Three-Layer Visual Rule

UI 設計の中心は以下の三層である。

```text
frame
section
card
```

## 6.1 Frame

役割:

```text
全ページで共通の骨格を与える
```

含むもの:

- ヘッダ
- フッタ
- 最大幅
- ページ左右余白
- 主要ナビ導線

## 6.2 Section

役割:

```text
意味のある情報群をまとめる
```

例:

- Global Status
- Summary / Highlights
- Controls / Chart
- Articles
- Prediction Dashboard
- Timeline

## 6.3 Card

役割:

```text
情報を読む最小単位
```

例:

- KPI card
- summary card
- health card
- chart card
- article card
- prediction card
- watchpoint card
- timeline card

カードは見た目を共通化し、中身だけをページごとに変える。

---

# 7. Global Status Standard

Global Status は GenesisPrediction UI の最上段標準ブロックである。

標準構成:

```text
GLOBAL RISK
SENTIMENT BALANCE
FX REGIME
ARTICLES
UPDATED
```

表示形式:

```text
横 5 カード
```

原則:

- 可能な限り 1 行で表現する
- 縦流しの説明列にしない
- 高さを取りすぎない
- Home / Overlay / Digest / Prediction / Prediction History で同系統表示とする

理由:

- ページ冒頭の高さを圧縮できる
- 下の本文へ早く到達できる
- ページ間の統一感が上がる

Prediction History でもこの 5-card 標準を採用する。

---

# 8. Standard Section Patterns

主要ページでよく使う標準断面は以下。

## 8.1 Hero Section

```text
Page title
1-2 行の lead 文
必要なら source / quick pill 群
```

## 8.2 Dashboard Split

```text
左 = controls / meta / source / explanation
右 = chart / image / summary KPI / result
```

この型は Sentiment / Overlay で有効。

## 8.3 Summary + KPI Split

```text
左 = Summary
右 = Highlights(KPI only)
```

この型は Digest の標準とする。

## 8.4 Main Result + Side Metrics

```text
左 = 主結論
右 = risk / confidence / action buttons
```

この型は Prediction / Prediction History で有効。

## 8.5 Bottom Detail Area

```text
articles
watchpoints
scenario lists
history timeline
supporting detail
```

本文の詳細は下段へ送る。

---

# 9. Page-by-Page Standard

## 9.1 Home

目的:

```text
最新状態の総合入口
```

標準ブロック:

- Hero
- Global Status
- KPI row
- Events(today)
- Data Health
- Sentiment
- Daily Summary

## 9.2 Overlay

目的:

```text
FX decision + remittance overlay の表示
```

標準ブロック:

- Hero
- Global Status
- KPI row
- Controls
- FX Overlay image

## 9.3 Sentiment

目的:

```text
articles + trend 表示
```

標準ブロック:

- Hero
- source / quick pills
- Controls
- Combined Trend
- helper cards
- Articles

## 9.4 Digest

目的:

```text
summary + highlights + articles の集約
```

標準ブロック:

- Hero
- Global Status
- Summary | Highlights
- Articles

Digest の Highlights は KPI only とする。

Highlights 内に article 一覧を再配置しない。

## 9.5 Prediction

目的:

```text
最新 prediction runtime の表示
```

標準ブロック:

- Hero
- Global Status
- Prediction Dashboard
- Overall Risk / Confidence
- KPI row
- Scenario probabilities
- What to watch
- Drivers / invalidation / implications

## 9.6 Prediction History

目的:

```text
prediction drift / confidence change / risk evolution の時系列表示
```

標準ブロック:

- Hero
- Global Status
- Prediction History Dashboard
- Drift summary / confidence drift
- KPI row
- Risk timeline
- Persistent watchpoints
- Historical snapshots

Prediction History の Global Status も縦説明ではなく横 5-card を標準とする。

---

# 10. Commonization Policy

共通化するもの:

```text
header
footer
container width
outer spacing
section spacing
card appearance
button appearance
pill appearance
nav appearance
active style
Global Status 5-card pattern
```

共通化しないもの:

```text
container 内部の細かい grid
チャート描画ロジック
記事カードの細部
prediction 本文の内容構造
history 集計ロジック
page-specific controls
```

原則:

```text
見た目の骨格は共通化
中身の意味構造はページごとに最適化
```

---

# 11. Alignment Rules

以下を全ページで揃える。

## 11.1 Header Alignment

- ブランドは左
- ナビ列は中央
- 状態 pill 群は右
- ヘッダ全体を左寄せの単列に崩さない

## 11.2 Container Alignment

- 本文コンテナは index と同じ水平位置を基準にする
- 独自余白で左に寄せない
- 主要ページは同じ最大幅系を使う

## 11.3 Card Height Discipline

- 冒頭ブロックは高さを取りすぎない
- Global Status は説明文の縦積みを避ける
- KPI は可能な限り短いラベルと短い補足でまとめる

## 11.4 Action Button Discipline

- Open JSON / Open CSV / Open image などの補助ボタンは card 内に置く
- 主ボタンと補助ボタンの見た目差は app.css に従う

---

# 12. Data / Layout Responsibility Split

責務分離は以下の通り。

## 12.1 scripts / analysis

- 正式データを生成する
- summary / sentiment / prediction / history を決定する
- latest / history alias を整備する

## 12.2 UI

- latest または history を読む
- card / section / chart / article として表示する
- 欠損時だけ fallback 表示を行う

## 12.3 Docs

- UI 標準を `docs/ui_layout_standard.md` に記録する
- データ依存を `docs/ui_data_dependencies.md` に記録する

---

# 13. Fallback Rule

UI の fallback は表示継続のためだけに使う。

原則:

```text
fallback は UI 継続のための read-only 処理
正式ソースの代替確定ではない
```

例:

- Digest は `view_model_latest.json` を優先し、必要時のみ summary / news に fallback
- Overlay は pair ごとの decision / image candidates を順に探索
- Prediction History は history snapshots が少ない場合でも空ページにしない

fallback を増やす場合は `ui_data_dependencies.md` に記録する。

---

# 14. Prohibited Patterns

以下は禁止または非推奨とする。

- ページごとの独自 topbar 再実装
- 共通ヘッダを使わない独自ヘッダ
- 大きく左寄せに崩れる container
- Global Status の縦長リスト化
- Highlights に article 一覧を重複表示すること
- UI 内で分析値を再決定すること
- 一時対応を標準化せず放置すること

---

# 15. Change Management Rule

UI 標準に影響する変更をした場合は、必要に応じて以下を更新する。

```text
docs/ui_layout_standard.md
docs/ui_data_dependencies.md
```

更新対象の例:

- 主要ページ追加
- 共通ナビ変更
- Global Status 構造変更
- 共通部品変更
- fallback 方針変更
- data path 変更

---

# 16. Current Standard Pages

2026-03-08 時点で、統一対象の主要ページは以下。

```text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

この 6 ページを GenesisPrediction GUI 第一章の標準完成形とみなす。

---

# 17. Practical Checklist

新規 UI ページ、または大規模修正時は以下を確認する。

```text
[ ] app.css を使っているか
[ ] common/header.html を使っているか
[ ] common/footer.html を使っているか
[ ] common/layout.js を使っているか
[ ] header の中央ナビ / 右 pill 群が崩れていないか
[ ] container が index 基準で揃っているか
[ ] Global Status が横 5-card になっているか
[ ] ページ固有ロジックを UI で再計算していないか
[ ] fallback を docs に記録したか
[ ] 大規模変更なら ui_data_dependencies.md も更新したか
```

---

# 18. Final Rule

GenesisPrediction UI の標準は以下に要約できる。

```text
共通骨格を守る
ページ固有の意味だけを変える
分析は analysis に置く
UI は読むことに徹する
```

この原則を守ることで、
GUI は増築しても壊れにくく、
AI も人間も迷わず保守できる状態を維持できる。
