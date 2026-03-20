# UI System (GenesisPrediction v2)

Version: 2.1
Status: Active
Purpose: GenesisPrediction v2 の UI 構造・責務・共通レイアウト・ページ役割を固定する
Last Updated: 2026-03-21

---

# 0. Purpose

このドキュメントは GenesisPrediction v2 の UI システム全体を定義する。

目的

- UI構造の誤解を防ぐ
- ページ責務を固定する
- Layout構造を統一する
- scripts / data / analysis との責務分離を維持する
- Explanation / 多言語対応を含めた現行構造を正として記録する

---

# 1. 最重要原則

UIは

表示レイヤ

である。

絶対ルール

UIは計算しない  
UIは分析しない  
UIは判断しない  


scripts → 生成
analysis → 真実（SST）
UI → 表示のみ

analysis = Single Source of Truth


:contentReference[oaicite:0]{index=0}

---

# 2. UIの責務

## 2.1 表示
JSON / CSV / PNG を整形して表示する

## 2.2 ナビゲーション
ページ間導線を統一する

## 2.3 fallback
データ欠損時でも表示を維持する

## 2.4 比較可視化
history比較（Prediction History）

---

# 3. UI配置


app/static/
├─ index.html
├─ overlay.html
├─ sentiment.html
├─ digest.html
├─ prediction.html
├─ prediction_history.html
├─ app.css
└─ common/
├─ header.html
├─ footer.html
└─ layout.js


---

# 4. ページ一覧

- Home
- Overlay
- Sentiment
- Digest
- Prediction
- Prediction History

---

# 5. 共通レイアウト

構造


header
container
content
footer
layout.js


### layout.js
- header/footer注入
- active判定
- UI統一

---

# 6. CSS責務


app/static/app.css


役割

- theme
- layout
- typography
- grid
- card

原則

共通 → app.css  
個別 → 最小限のみ

---

# 7. 各ページ責務

## Home
概要・入口  
詳細は持たない

## Overlay
FX判断表示  
fallback許可（表示のみ）

## Sentiment
記事感情表示  
再分類禁止

## Digest
summary / KPI / highlights  
再計算禁止

## Prediction
prediction_latest.json表示  
生成禁止

## Prediction History
履歴比較  
再予測禁止

---

# 8. データ原則


latest優先
historyは閲覧専用
fallbackは表示専用


---

# 9. fallback原則

許可

- 画像代替
- JSON欠損対応

禁止

- 再計算
- 再分類
- 予測生成

---

# 10. Global Status

- 全ページ共通
- 補助表示
- 本体の代替禁止

---

# 11. Explanation Layer

Explanationは


analysis/explanation/*.json


から読む

UIは禁止

- explanation生成
- 意味の再定義

---

# 12. 多言語対応


UI = selector only
translation = analysis


UIは

- lang選択
- _i18n表示のみ

翻訳禁止

---

# 13. 最終原則


UIは受け取った真実を表示するだけ


---

END OF DOCUMENT