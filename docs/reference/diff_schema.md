# Genesis Diff JSON v1

## 概要
Genesis Diff は、前日（baseline）との差分を  
**機械可読（diff）＋ 人間可読（interpretation）** の両立を目的とした JSON 形式。

- 出力先: `analysis/diff_YYYY-MM-DD.json`
- 比較対象:
  - today: 当日データ
  - baseline: 原則として前日データ

---

## トップレベル構造

---

## extensions

拡張領域。後方互換を保ったまま機能追加するための枠。

### extensions.interpretation (optional)
人間可読な要約・箇条書き・仮説など。

### extensions.signals (optional)
集計指標による状態量（例: churn_rate, volatility など）。

### extensions.signal_candidates (optional)
Prediction 層へ接続するための「信号候補」。
diff / extensions.signals / event_level を根拠に、severity/confidence を付与して正規化する。

#### Type
`signal_candidates: SignalCandidate[]`

#### SignalCandidate fields
- `id`: string  
  例: `sig_topic_rotation_high_churn`
- `label`: string  
  人が読む短い名前
- `kind`: string  
  例: `dynamics` / `volume` / `sentiment` / `entities` / `keywords`
- `severity`: number  
  0.0 - 1.0（注意度）
- `confidence`: number  
  0.0 - 1.0（確からしさ）
- `evidence`: object  
  根拠（監査可能にする）
  - `refs`: string[]（参照パス例: `extensions.signals`, `event_level.added`）
  - `metrics`: object（任意。計算に使った数値）
- `explain`: string  
  1〜2文の説明
- `scope`: object (optional)  
  将来拡張用（dataset/category/entity/keyword など）


```json
{
  "schema_version": 1,
  "diff": {},
  "summary": {},
  "quality": {},
  "extensions": {}
}
