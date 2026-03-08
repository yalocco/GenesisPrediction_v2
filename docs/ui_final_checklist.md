# UI Final Checklist (GenesisPrediction v2 / LABOS)

Version: 1.0
Status: Active
Last Updated: 2026-03-08

---

# 0. 目的

本ドキュメントは  
GenesisPrediction v2 / LABOS UI を公開前に最終確認するための  
**UI完成チェックリスト**である。

対象ページ：

- `app/static/index.html`
- `app/static/overlay.html`
- `app/static/sentiment.html`
- `app/static/digest.html`
- `app/static/prediction.html`
- `app/static/prediction_history.html`

共通部品：

- `app/static/app.css`
- `app/static/common/header.html`
- `app/static/common/footer.html`
- `app/static/common/layout.js`
- `app/static/common/global_status.js`

---

# 1. UI基本原則

GenesisPrediction UI は  
**Topbar / Container / Card の三層構造**で運用する。

```text
Topbar
↓
Container
↓
Card
````

定義：

* Topbar
  全ページ共通ナビとステータス表示

* Container
  ページ固有内容の共通幅領域

* Card
  情報表示の最小単位

---

# 2. 共通構造チェック

## 2.1 Header / Footer

全ページで以下が成立していること。

* `#site-header` を使用している
* `#site-footer` を使用している
* `layout.js` で共通読み込みしている
* nav active が現在ページで正しく点灯する
* ページごとに header を直書きしていない

## 2.2 Topbar 3ゾーン

Topbar は必ず以下の3ゾーンであること。

```text
左: ロゴ
中央: 6ページナビ
右: Ready / Health / as_of
```

確認項目：

* ロゴが左固定
* 6ページボタンが中央配置
* status pill が右配置
* すべてのページで並び順が同じ
* 高さ・余白・pillサイズが揃っている

## 2.3 Container 幅

全ページで同一の container 幅を使用すること。

基準：

```css
.container {
  width: min(1240px, calc(100% - 28px));
  margin: 0 auto;
}
```

確認項目：

* header と本文の左右位置が揃う
* footer と本文の左右位置が揃う
* どのページも同じ余白に見える
* 新ページでも container を使う

## 2.4 Card 表示

card は共通トーンを守ること。

確認項目：

* border が弱い青系
* 背景が dark glass
* radius が揃っている
* shadow が揃っている
* card 内の上下余白が揃っている

---

# 3. 共通UI部品チェック

## 3.1 Nav

* Home
* Overlay
* Sentiment
* Digest
* Prediction
* Prediction History

確認項目：

* 6ボタンすべて存在
* 順番が固定
* active 表示が揃う
* hover 表示が揃う
* ボタン高さが揃う

## 3.2 Status pills

* Ready
* Health
* as_of

確認項目：

* 3つとも全ページで表示
* 右寄せされている
* pill 高さが揃う
* 文字サイズが揃う
* 長い値でも崩れない

## 3.3 Buttons

確認項目：

* `Open JSON`
* `Open CSV`
* `Open image`
* `Open decision JSON`

などのボタンが共通見た目であること。

見る点：

* border
* radius
* padding
* text size
* hover

---

# 4. ページ別チェック

## 4.1 Home

目的：

* 今日の概況を最初に把握するページ

必須要素：

* Global Status
* KPI 4枚
* Events (today)
* Data Health
* Sentiment
* Daily Summary

確認項目：

* 情報欠落がない
* Summary の可読性がある
* source pill がある
* Open JSON が必要箇所にある
* card 間の余白が揃っている

## 4.2 Overlay

目的：

* FX decision + remittance overlay の確認

必須要素：

* Global Status
* Decision / Image / Decision JSON KPI
* Pair selector
* Decision
* Reason
* Source
* Overlay image

確認項目：

* 画像が横幅に収まる
* 画像が異常に巨大化しない
* JPYTHB / USDJPY / USDTHB / MULTI 切替が機能する
* fallback 表示が壊れない
* source 表示がわかる
* pair note が読みやすい

## 4.3 Sentiment

目的：

* Sentiment trend / article 状況の確認

必須要素：

* Global Status
* trend 情報
* controls
* summary / KPI / source
* article list または trend 表示

確認項目：

* trend が崩れない
* controls が横並びで破綻しない
* source がわかる
* article / trend の優先関係が明確
* レイアウトが Home / Overlay と同トーン

## 4.4 Digest

目的：

* Summary + top highlights の表示

必須要素：

* Global Status
* Summary
* KPI
* Top highlights
* search/filter 系 controls

確認項目：

* ハイライト一覧が崩れない
* サムネイルが適正サイズ
* title/source/risk の視認性がある
* controls が詰まりすぎない
* Summary が読める長さに収まる

## 4.5 Prediction

目的：

* prediction runtime の最新出力確認

必須要素：

* Global Status
* Summary headline
* Overall Risk
* Confidence
* Scenario probabilities
* Watchpoints
* Drivers
* Invalidations
* Key implications

確認項目：

* prediction_latest.json を読むだけ
* UI側で再計算しない
* best/base/worst が見分けやすい
* risk 表示が強調される
* Open History 導線がある
* card の情報密度が高くても読める

## 4.6 Prediction History

目的：

* 過去の prediction 出力推移確認

必須要素：

* Global Status
* History headline
* KPI
* filter / search / sort
* history timeline
* selected snapshot

確認項目：

* prediction_history_index.json を読むだけ
* filter / sort で崩れない
* selected detail が見やすい
* Open JSON が機能する
* 履歴件数が増えても読める構造

---

# 5. レスポンシブチェック

## 5.1 Desktop

確認項目：

* header 3ゾーンが一列で収まる
* 6ページボタンが自然
* KPI grid が崩れない
* image / chart が大きすぎない
* card の左右位置が揃う

## 5.2 Tablet

確認項目：

* nav が折り返しても破綻しない
* status pill が下に落ちても読める
* grid2 / grid4 が適切に段組み変更される

## 5.3 Mobile

確認項目：

* 1カラムで読める
* 横スクロールが出ない
* ボタンが押せる大きさ
* header が異常に高くならない
* chart / image が画面外へはみ出さない

---

# 6. データ表示チェック

## 6.1 欠損時

確認項目：

* missing 表示が壊れない
* MISS / Error / not available が一貫している
* UIが空白で崩れない
* fallback がある箇所は fallback される

## 6.2 source 表示

確認項目：

* source pill が残っている
* どの JSON / CSV / image を読んだかわかる
* debugging に使える

## 6.3 Open系導線

確認項目：

* Open JSON
* Open CSV
* Open image
* Open decision JSON

が壊れていないこと。

---

# 7. デザイン統一チェック

確認項目：

* 背景トーンが一致
* 見出しサイズが近い
* card radius が一致
* button/pill radius が一致
* border color が一致
* hover トーンが一致
* 文字色が一致
* source pill のトーンが一致

---

# 8. 禁止事項

* header をページごとに個別実装し続ける
* container を使わず幅をページごとに決める
* UI側で計算ロジックを持つ
* analysis / prediction を手動で真実化する
* 1ページだけ別デザインにする
* 差分パッチ運用を前提にする

---

# 9. 完成条件

以下を満たしたら UI 完成とみなす。

* 6ページが同じ Topbar を使う
* 6ページが同じ Container 幅を使う
* 6ページが同じ Card トーンを使う
* status pill が全ページで揃う
* 情報欠落がない
* ローカル表示で崩れない
* deploy 後も崩れない

---

# 10. 運用メモ

UI作業は必ず以下のルールで行う。

* 1ターン = 1作業
* 差分禁止
* 必ず完全ファイル
* 長大GUIは必要時ダウンロード運用
* UIは read-only
* analysis / prediction を読むだけで再計算しない

---

# 11. 結論

GenesisPrediction UI は
**Topbar / Container / Card** の三層構造で統一する。

公開品質のためには

* 共通 header
* 共通 footer
* 共通 layout
* 共通 app.css

を UIコアとして固定し、
ページ固有ロジックは container 内に閉じ込める。

これを守ることで

* UI統一
* 追加ページ対応
* メンテナンス性向上
* 公開時の修正漏れ防止

を実現する。

---

END OF DOCUMENT

```
