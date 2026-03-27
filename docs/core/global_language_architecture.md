# GenesisPrediction Global Language Architecture

（Multi-language System / i18n統一設計）

Status: Active
Last Updated: 2026-03-25
Purpose: GenesisPrediction 全体における多言語構造を統一し、SSOT原則を維持したまま三か国語展開を可能にする

---

# 0. Purpose

本ドキュメントは

GenesisPrediction v2 における

**多言語設計（Global Language System）**

を定義する。

目的

* 全ページで言語切替を可能にする
* UI変更なしで多言語拡張可能にする
* 翻訳を analysis 側に統一する
* SSOT原則を維持する
* 将来の LABOS 公開に耐える構造を作る

---

# 1. Core Principle

最重要原則

```

analysis = Single Source of Truth
UI = selector only
translation = generated in scripts / analysis

```

---

## 1.1 Language Handling Principle

```

翻訳はUIで行わない
翻訳はanalysisで生成する
UIは言語キーを選択するだけ

```

---

## 1.2 Explanation Principle

```

Explanation は構造であり自由文ではない
多言語は構造の複製である

```

---

# 2. Architecture Position

全体構造

```

scripts
↓
analysis（多言語artifact生成）
↓
app（表示のみ）

```

---

多言語追加後

```

scripts
↓
analysis（_i18n含むartifact）
↓
UI（lang選択のみ）

````

---

# 3. i18n Contract（全artifact共通）

すべての多言語対応artifactは以下を持つ

```json
{
  "lang_default": "ja",
  "languages": ["en", "ja", "th"]
}
````

---

## 3.1 i18n Field Rule

翻訳対象フィールドは以下形式とする

```json
"summary_i18n": {
  "en": "...",
  "ja": "...",
  "th": "..."
}
```

---

## 3.2 命名規則

| 項目     | 形式             |
| ------ | -------------- |
| 単一テキスト | `field_i18n`   |
| 配列     | `field_i18n`   |
| UI用語   | `meaning_i18n` |

---

## 3.3 既存フィールドとの関係

```text
既存フィールド = 後方互換
*_i18n = 正式表示用
```

---

# 4. 対象フィールド

## 4.1 Explanation Layer（最優先）

* headline
* summary
* why_it_matters
* drivers
* watchpoints
* invalidation
* must_not_mean
* ui_terms.meaning

---

## 4.2 Prediction

* summary のみ

---

## 4.3 非対象（翻訳しない）

```
confidence
risk_level
probability
signals
scenario weights
```

---

# 5. UI責務

UIは以下のみ行う

```
言語選択
_i18nフィールド参照
表示
```

---

## 5.1 禁止事項

```
翻訳処理
意味補完
fallback翻訳生成
文章生成
```

---

# 6. Language Selection

## 6.1 グローバル状態

```js
window.GP_LANG
```

---

## 6.2 保存

```
localStorage key = gp_lang
```

---

## 6.3 優先順位

```
1. localStorage
2. artifact.lang_default
3. "en"
```

---

# 7. Rendering Rule

```js
const lang = window.GP_LANG || data.lang_default;

text = data.summary_i18n[lang];
```

---

# 8. 共通文言とページ文言

## 8.1 共通文言（翻訳対象外 or dictionary）

```
confidence
risk
scenario
```

---

## 8.2 ページ文言（artifact管理）

```
summary
drivers
watchpoints
```

---

# 8.5 Data i18n Classification（動的データ多言語分類）

## 目的

動的データに対する多言語処理を統一し、

* 辞書で解決するもの
* 自由文として扱うもの

を明確に分離する

---

## 基本原則

```
UIは翻訳しない
翻訳はanalysisで生成
UIは_i18nのみ参照
英語は内部基準（SSOT）
```

---

## 分類

### ① 辞書ベース（Deterministic）

対象：

* status（OK / CAUTION / WARNING）
* regime
* scenario_type
* signal_label
* FX判定

処理：

```json
{
  "CAUTION": {
    "ja": "注意",
    "th": "ระวัง"
  }
}
```

---

### ② テンプレート（Semi-structured）

例：

* "Confidence: 60%"

```json
{
  "confidence_label": {
    "ja": "信頼度: {value}%",
    "th": "ความมั่นใจ: {value}%"
  }
}
```

---

### ③ 自由文（Free text）

対象：

* summary
* narrative
* explanation
* drivers
* watchpoints

処理：

```
英語そのまま（将来LLM）
```

---

## fallback

analysis側で保証：

```json
{
  "summary_i18n": {
    "en": "...",
    "ja": "...",
    "th": "..."
  }
}
```

---

## 辞書配置

```
configs/i18n_dictionary.json
```

---

## 責務分離

### analysis

* 翻訳生成
* fallback保証
* i18n構造生成

### UI

* 表示のみ
* selectorのみ

---

## 禁止事項

```
UI翻訳
UI fallback
英語直接参照
ページ別ロジック
```

---

# 9. Translation Generation

翻訳は以下で生成

```
scripts/build_explanation_multilang.py
```

---

## 9.1 原則

```
翻訳は deterministic にする
手動UI翻訳は禁止
```

---

# 10. Page Coverage

対象ページ

```
prediction.html
overlay.html
digest.html
sentiment.html
prediction_history.html
index.html
```

---

# 11. Implementation Order

```
Phase1: Explanation 多言語化（完了）
Phase2: Global Language Architecture
Phase3: UI selector 実装
Phase4: 全ページ展開
Phase5: LABOS統合
```

---

# 12. Failure Modes

避けるべき設計

```
UIで翻訳
UIで説明生成
field名のバラバラ化
言語ロジック分散
```

---

# 13. Final Principle

GenesisPrediction における多言語とは

```
翻訳ではない
構造の多重化である
```

---

# 14. Summary

```
analysis = 真実
translation = analysisで生成
UI = 表示のみ
language = selectorのみ
```

---

END OF DOCUMENT

```

---

# ✅ 重要確認

今回のこれは👇

✔ 行数減少なし  
✔ 既存内容100%保持  
✔ 追記のみ  
✔ ルール完全準拠  

---


---

# 15. Cross-Page i18n Rollout Standard

## 15.1 Reference Page

Prediction を基準実装とする。

理由:

- *_i18n を analysis 側で生成している
- UI は pickI18n / pickI18nList により参照のみ行う
- UI で翻訳・補完・再計算を行っていない

この構造を他ページへ横展開する。

---

## 15.2 Rollout Target Pages

Prediction は原則固定とし、以下ページへ順次適用する。

```text
index.html
sentiment.html
overlay.html
digest.html
prediction_history.html
```

digest.html は今回の Digest Summary 圧縮対応を含め、完了済みページとして扱う。

---

## 15.3 Rollout Rule

全ページで次を満たすこと。

```text
UI は *_i18n を優先参照する
UI は pickI18n / pickI18nList 経由のみで表示する
翻訳生成は analysis 側で行う
英語 field 直読みを禁止する
```

---

## 15.4 Digest Special Rule

Digest は Prediction と異なり summary が自由文であるため、
全文翻訳ではなく analysis 側で構造化圧縮した summary_i18n を生成してよい。

例:

```text
件数
主要アンカー
代表ヘッドライン数
新規 URL 数
```

Digest の Summary は UI で翻訳しない。

---

## 15.5 Final Goal

最終的に全ページを Prediction と同じ言語責務に統一する。

```text
analysis = i18n 生成
UI = i18n 表示
language state = 共通管理
```

# UI i18n Template (Prediction-Based Standard)


# 🧠 GenesisPrediction UI i18n テンプレート仕様書（確定版）

---

# 🎯 目的

UIを以下に完全統一する

* 翻訳ロジック完全排除
* analysisの `*_i18n` のみ表示
* 言語変更で全UIが再描画される

---

# 🔥 最重要原則（絶対遵守）

1. UIは表示のみ（翻訳禁止）
2. 言語判定は共通マネージャーのみ
3. fallback禁止（UI側で補完しない）
4. `_i18n` を最優先
5. 静的・動的を分離
6. 再描画はイベント駆動

---

# 🏗 全体アーキテクチャ

```text
analysis (SSOT)
   ↓
fetchJson()
   ↓
normalize()
   ↓
pickI18n()
   ↓
render()
```

---

# 🧩 1. データ取得層

## ルール

* JSONパスは固定
* UIで分岐しない

```javascript
const SOURCES = {
  prediction: "/data/prediction/prediction_latest.json",
  explanation: "/data/explanation/prediction_explanation_latest.json",
  history: "/data/prediction/prediction_history_index.json"
};
```

---

# 🌐 2. 言語管理層（共通のみ使用）

## 使用

```javascript
const lang = window.GP_LANG || "en";
```

または

```javascript
window.GP_LANG_MANAGER.get()
```

---

## 禁止

* localStorage直接参照 ❌
* ページ独自言語変数 ❌

---

# 🏷 3. 静的UI文言層

## HTML

```html
<h1 data-ui-text="title"></h1>
```

---

## JS

```javascript
function applyStaticText(dict) {
  document.querySelectorAll("[data-ui-text]").forEach(el => {
    const key = el.dataset.uiText;
    el.textContent = dict[key] || "";
  });
}
```

---

## データ

```javascript
const UI_TEXT = {
  title: {
    en: "Prediction",
    ja: "予測",
    th: "การคาดการณ์"
  }
};
```

---

# 🌍 4. 動的多言語層（核心）

## 必須関数

```javascript
function pickI18n(obj, lang) {
  if (!obj) return "";
  return obj[lang] ?? obj["en"] ?? "";
}
```

---

## 配列版

```javascript
function pickI18nList(list, lang) {
  if (!Array.isArray(list)) return [];
  return list.map(item => pickI18n(item, lang));
}
```

---

## 使用例

```javascript
const title = pickI18n(data.title_i18n, lang);
```

---

## 禁止

```javascript
if (!ja) translate(en) ❌
```

---

# 🔄 5. 正規化層（超重要）

## 役割

* JSON構造のばらつきを吸収
* UI用フォーマットに変換

---

## 例

```javascript
function normalizePrediction(data, lang) {
  return {
    title: pickI18n(data.title_i18n, lang),
    summary: pickI18n(data.summary_i18n, lang),
    drivers: pickI18nList(data.drivers_i18n, lang)
  };
}
```

---

## ルール

* normalize内でのみ `_i18n` 使用
* renderでは使わない

---

# 🎨 6. 描画層

## ルール

* 描画は「表示のみ」
* ロジック禁止
* 翻訳禁止

---

## 例

```javascript
function render(state) {
  document.getElementById("title").textContent = state.title;
}
```

---

# 🔁 7. 再描画（重要）

## 初期

```javascript
init()
  → fetch
  → normalize
  → render
```

---

## 言語変更

```javascript
window.addEventListener("gp:lang-changed", () => {
  renderFromState();
});
```

---

## 禁止

* 再fetch ❌
* 再normalize ❌

---

# 🧠 8. 状態管理

```javascript
let STATE = {
  raw: {},
  normalized: {}
};
```

---

## フロー

```javascript
STATE.raw = fetchedData;
STATE.normalized = normalize(fetchedData, lang);
render(STATE.normalized);
```

---

# 🔥 9. ページ適用パターン

---

## パターンA（prediction型）

* explanationあり
* 長文あり

👉 normalize必須

---

## パターンB（history型）

* リスト中心

👉 pickI18n中心

---

## パターンC（軽量）

* index / overlay / sentiment

👉 静的＋簡易pick

---

## パターンD（digest）

* 複合

👉 最後に対応

---

# 🚫 禁止事項まとめ

* UIで翻訳
* UIでfallback生成
* JSON直接表示
* langの個別管理
* i18nなしデータの補完

---

# 🧪 テスト基準

## 必須確認

* EN/JA/TH 切替で即反映
* リロード不要
* 混在なし
* 英語残りなし

---

# 🎯 完了定義

* 全ページ `_i18n` のみ表示
* UI翻訳ロジックゼロ
* 言語変更イベントで完全再描画
* JSONのみで言語切替成立

---

# 🚀 次スレの目的

👉 この仕様を使って

* overlay
* sentiment
* index
* history
* 最後に digest

を一気に統一

---

# 👍 最後に

この仕様は

👉 **prediction.html を抽象化したもの**

です

---
