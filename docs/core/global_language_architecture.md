# GenesisPrediction Global Language Architecture

（Multi-language System / i18n統一設計）

Status: Active
Last Updated: 2026-03-21
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
```

---

# 3. i18n Contract（全artifact共通）

すべての多言語対応artifactは以下を持つ

```json
{
  "lang_default": "ja",
  "languages": ["en", "ja", "th"]
}
```

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
Phase2: Global Language Architecture（本ドキュメント）
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
