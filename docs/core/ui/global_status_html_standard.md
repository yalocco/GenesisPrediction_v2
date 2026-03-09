# Global Status HTML Standard
GenesisPrediction v2

Version: 1.0  
Status: Active  
Location: docs/core/ui/

---

# 1. Purpose

この文書は、GenesisPrediction UI における Global Status の  
**HTML / DOM / JS 実装標準**を定義する。

対象は次の共通要素である。

- HTML 構造
- DOM class 命名
- JS 描画責務
- loading / empty / unavailable 表示
- page 個別実装との責務分離

本書の目的は、見た目の統一だけでなく、  
**実装のばらつきを止めること**である。

---

# 2. Scope

対象ページ

- Home
- Overlay
- Sentiment
- Digest
- Prediction
- Prediction History

これらのページは、Global Status を  
**同一 DOM 構造・同一 class 構造・同一更新方式**で扱う。

---

# 3. Standard Rendering Policy

Global Status は次の方針で描画する。

- HTML 側で **5カードの骨組みを固定配置**する
- JS は **値の差し込みのみ**を担当する
- JS が DOM 構造を組み立て直してはならない
- ページごとに HTML 構造を変えてはならない
- データがなくても UI の箱は消さない

つまり、Global Status は

**structure fixed / data replace only**

で運用する。

---

# 4. Standard HTML Structure

Global Status の標準 HTML は以下とする。

```html
<section class="panel global-status-panel" aria-labelledby="global-status-title">
  <div class="panel-header">
    <h2 id="global-status-title" class="section-title">Global Status</h2>
  </div>

  <div class="global-status" data-role="global-status">
    <article class="status-card" data-slot="1">
      <div class="status-label" data-field="label">Date</div>
      <div class="status-value" data-field="value">—</div>
      <div class="status-sub" data-field="sub">loading</div>
    </article>

    <article class="status-card" data-slot="2">
      <div class="status-label" data-field="label">System</div>
      <div class="status-value" data-field="value">—</div>
      <div class="status-sub" data-field="sub">loading</div>
    </article>

    <article class="status-card" data-slot="3">
      <div class="status-label" data-field="label">Analysis</div>
      <div class="status-value" data-field="value">—</div>
      <div class="status-sub" data-field="sub">loading</div>
    </article>

    <article class="status-card" data-slot="4">
      <div class="status-label" data-field="label">Prediction</div>
      <div class="status-value" data-field="value">—</div>
      <div class="status-sub" data-field="sub">loading</div>
    </article>

    <article class="status-card" data-slot="5">
      <div class="status-label" data-field="label">Health</div>
      <div class="status-value" data-field="value">—</div>
      <div class="status-sub" data-field="sub">loading</div>
    </article>
  </div>
</section>
````

---

# 5. DOM Rules

必須 class

* `global-status-panel`
* `global-status`
* `status-card`
* `status-label`
* `status-value`
* `status-sub`

必須 attribute

* `data-role="global-status"`
* `data-slot="1"` ～ `data-slot="5"`

任意で許可

* `id`
* `aria-labelledby`

禁止

* ページ専用 class 名の追加で見た目を変えること
* `style=""` の inline 指定
* DOM 階層の増減
* slot 数変更

---

# 6. Card Semantics

各カードは以下の 3要素を持つ。

* label
  項目名
* value
  主表示値
* sub
  補足説明

原則

* label は短く固定的
* value は一目でわかる値
* sub は状態補足または由来補足
* 複数行説明は禁止
* 長文は禁止

良い例

* Date / 2026-03-09 / UTC
* Health / OK / analysis ready
* Prediction / WARN / low confidence

悪い例

* 今日の分析の状態
* 直近の複雑な説明文
* 複数段落の補足

---

# 7. Standard JS Responsibility

JS の責務は **値の注入だけ** とする。

JS がやること

* JSON を読む
* 5カード分の表示データを整形する
* 各カードの label / value / sub を更新する
* state class を必要最小限で付与する

JS がやってはいけないこと

* カードを追加する
* カードを削除する
* HTML を innerHTML で全面再生成する
* ページごとに別構造を出し分ける
* style 値を script から直接変更する

---

# 8. Standard Data Shape in JS

JS 内では、Global Status 用データを
次の共通 shape に正規化してから描画する。

```js
[
  { label: "Date",       value: "2026-03-09", sub: "UTC",             state: "ready" },
  { label: "System",     value: "ONLINE",     sub: "ui synced",       state: "ready" },
  { label: "Analysis",   value: "READY",      sub: "daily summary",   state: "ready" },
  { label: "Prediction", value: "WARN",       sub: "low confidence",  state: "warn"  },
  { label: "Health",     value: "OK",         sub: "all inputs valid",state: "ready" }
]
```

要素数は **必ず5** とする。

不足時も 5件に補完する。

---

# 9. Standard Render Function

標準描画関数の責務イメージは以下とする。

```js
function renderGlobalStatus(cards) {
  const root = document.querySelector('[data-role="global-status"]');
  if (!root) return;

  const normalized = normalizeGlobalStatusCards(cards);

  const cardNodes = root.querySelectorAll('.status-card');
  cardNodes.forEach((node, index) => {
    const item = normalized[index];

    const label = node.querySelector('.status-label');
    const value = node.querySelector('.status-value');
    const sub = node.querySelector('.status-sub');

    if (label) label.textContent = item.label;
    if (value) value.textContent = item.value;
    if (sub) sub.textContent = item.sub;

    node.dataset.state = item.state || 'ready';
  });
}
```

重要なのは実装言語ではなく次の原則である。

* root を取得する
* cardNodes を固定数で扱う
* textContent で値を差し込む
* state は attribute で表す
* 構造は変更しない

---

# 10. Normalize Rule

描画前に必ず normalize する。

normalize の役割

* 要素数を 5 にする
* 未定義値を補完する
* state を標準語彙へ変換する
* null / undefined / 空文字を安全に処理する

標準補完値

* label: `Unknown`
* value: `—`
* sub: `no data`
* state: `empty`

---

# 11. State Vocabulary

Global Status の状態語彙は以下に限定する。

* `loading`
* `ready`
* `empty`
* `unavailable`
* `warn`

意味

* `loading`
  読み込み中
* `ready`
  正常表示
* `empty`
  データなし
* `unavailable`
  取得不能 / 参照失敗
* `warn`
  注意表示は可能だが異常ではない

これ以外の state 名は使わない。

---

# 12. Standard Text Rules by State

## loading

```text
value: —
sub  : loading
```

## empty

```text
value: —
sub  : no data
```

## unavailable

```text
value: —
sub  : unavailable
```

## warn

```text
value: WARN
sub  : reason short text
```

## ready

```text
value: actual value
sub  : short support text
```

---

# 13. CSS Hook Rules

見た目制御は CSS 側で行う。

JS が触れてよいのは次のみ。

* `data-state`
* `textContent`

例

```html
<article class="status-card" data-slot="4" data-state="warn">
```

CSS はこの `data-state` を見て装飾してよい。

例

```css
.status-card[data-state="warn"] { ... }
.status-card[data-state="empty"] { ... }
.status-card[data-state="unavailable"] { ... }
```

禁止

* JS から `element.style.color = ...`
* JS から `className = "...全部置換..."`

---

# 14. Page Responsibility Boundary

## app.css の責務

* global-status 全体レイアウト
* card 見た目
* label / value / sub タイポグラフィ
* state 別見た目
* responsive 制御

## page JS の責務

* 各ページの JSON 読み込み
* 5件への整形
* render 関数呼び出し

## page HTML の責務

* 標準骨組みを置く
* section title を持つ
* data-role を持つ

---

# 15. No-Data Safety Rule

Global Status はデータ不足でも消してはならない。

禁止

* データがないので section 全体を非表示にする
* 1枚だけ card を減らす
* 値がない card を remove する

許可

* `—`
* `no data`
* `unavailable`
* `loading`

これは UI を止めないための保険である。

---

# 16. Accessibility Rule

最低限のアクセシビリティ規則

* `section` を使う
* `aria-labelledby` を使う
* section title を必ず持つ
* 値表示は画像だけにしない
* 色だけで意味を伝えない

Global Status は文字情報だけでも読めること。

---

# 17. Responsive Rule

PC では 5列固定。

タブレット・狭幅では app.css 側で段組み変更してよい。

ただし禁止事項

* ページごとにレスポンシブ挙動を変える
* HTML をページ別に分岐する
* スマホだけ card 数を変える

変えてよいのは **列数だけ** である。

---

# 18. Standard Example Mapping

以下は例であり、固定項目名ではない。

## Home

* Date
* System
* Analysis
* Prediction
* Health

## Overlay

* Date
* FX Base
* FX Signal
* Trend
* Health

## Sentiment

* Date
* Coverage
* Positive
* Negative
* Health

## Digest

* Date
* Summary
* Topics
* Region
* Health

## Prediction

* Date
* Regime
* Signal
* Confidence
* Health

## Prediction History

* Date
* History
* Drift
* Match
* Health

注意：

**構造は共通、内容だけ変える。**

---

# 19. Forbidden Implementation Patterns

禁止パターン

* pageA は `<div>` 3層、pageB は `<li>` 2層
* page ごとに class 名が違う
* あるページだけ 4カード
* JS が innerHTML で card 群を再生成
* JSON 欠損時に section を丸ごと隠す
* page 独自 CSS が Global Status を上書きする

---

# 20. Recommended Implementation Order

Global Status 実装統一は次の順で行う。

1. Prediction
2. Prediction History
3. Home
4. Overlay
5. Sentiment
6. Digest

理由

* Prediction 系が最も崩れやすい
* ここを基準にすれば他ページが合わせやすい
* 既存統一済みページへの影響を最小化できる

---

# 21. Definition of Done

Global Status 実装が完了したとみなす条件

* 全対象ページが同一 HTML 構造
* 全対象ページが同一 class 構造
* 全対象ページが 5カード固定
* loading / empty / unavailable が統一
* page 個別 style override がない
* JS が構造を組み替えていない

---

# 22. Version History

v1.0
Initial HTML / DOM / JS implementation standard for Global Status

```
