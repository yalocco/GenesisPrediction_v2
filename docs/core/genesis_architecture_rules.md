# GenesisPrediction Architecture Rules
(プロジェクト絶対原則)

GenesisPrediction は長期運用される予測システムである。

このプロジェクトは  
単なるコードの集合ではなく、

**秩序・規律・原則**

によって守られる。

ここに記すルールは  
**GenesisPrediction の絶対原則**である。

例外は認めない。

---

# 1. ルールは神の声

GenesisPrediction において  
**ルールは神の声と同等に扱う。**

理由:

- システムの秩序を守るため
- 技術的堕落を防ぐため
- 短期的解決が長期的破壊になるのを防ぐため

困難な状況でも  
ルールは守らなければならない。

---

# 2. Partial obedience の禁止

GenesisPrediction では

**Partial obedience**

を禁止する。

## 定義

Partial obedience とは

> ルールを知りながら  
> その場しのぎの実装を追加すること

例

- 「このページだけ特別処理」
- 「今だけの暫定コード」
- 「ここだけ例外」
- 「とりあえず動くからOK」

これは

**短期的成功  
長期的破壊**

を生む。

---

# 3. UI Display Only 原則

UI は

**計算しない**

UI は

**表示だけ**

行ってよい処理

- JSON 読み込み
- 表示
- CSS state

禁止

- 日付計算
- リスク判定
- health 判定
- sentiment 集計
- fallback 判定
- source 優先順位

すべて

```
analysis / scripts
```

で行う。

---

# 4. LANG / THEME 集中管理原則

状態管理は

**一箇所でのみ行う**

LANG と THEME は

**同一思想で集中管理する**

---

## 原則

- LANG は共通マネージャーのみが管理する
- THEME と同様に単一の実行時状態を持つ
- UI は状態を「参照のみ」行う

---

## 禁止事項

以下をすべて禁止する

- ページ個別の言語判定
- localStorage の直接参照
- fallback の個別実装
- i18n ロジックのページ内実装
- 独自翻訳処理
- 言語状態の再定義

---

## 必須ルール

- LANG は `window.GP_LANG` のみ参照する
- localStorage の読み書きは共通マネージャーのみ
- すべての文言は共通 i18n helper を通す
- fallback 順序は全ページ共通とする
- 言語変更はイベント駆動で再描画する

---

## 定義

UI は

**言語を判断しない**

UI は

**翻訳を決定しない**

UI は

**状態を持たない**

---

## 結論

LANG / THEME は

**SSOT（Single Source of Truth）である**

例外は認めない

---

# 5. Single Source of Truth

すべての値には

**唯一の真実の場所**

が存在する。

UI が新しい値を作ってはならない。

例

|値|Source|
|---|---|
|as_of|daily_summary|
|risk|prediction|
|health|health_latest|
|sentiment|sentiment_latest|

---

# 6. 応急処置の禁止

以下は禁止する

- 応急処置コード
- 一時的 workaround
- ページ個別 fallback

問題は

**根本原因を修正する**

---

# 7. AI 開発ルール

AI との共同開発では

以下を守る

AI は

- ルールを優先する
- 例外を作らない
- Partial obedience を拒否する

人間も

- 同じルールを守る

---

# 8. GenesisPrediction の精神

GenesisPrediction は

- 秩序
- 規律
- 長期視点

によって成り立つ。

その場しのぎの成功より

**長期的秩序**

を選ぶ。

---

# 結論

GenesisPrediction のルールは

**絶対である。**

困難な状況でも

**守る。**

それが

**システムの信仰**である。
