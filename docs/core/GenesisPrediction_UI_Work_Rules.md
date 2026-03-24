# GenesisPrediction UI Work Rules

この文書は GenesisPrediction UI 作業の運用ルールを定義する。

目的

- UI破壊事故の防止
- レイアウト崩れの防止
- AIと人間の役割分離
- UIテーマ方式の維持


---

# 基本原則

GenesisPrediction UI は

Theme System

で構築されている。

UIは以下の3層構造で管理する。

Theme Layer  
Layout Layer  
Page Layer


```

app/static/app.css
app/static/common/layout.js
app/static/*.html

```

役割

Theme  
UIデザイン全体

Layout  
header / nav / footer

Page  
各ページの内容のみ


---

# UI編集ルール

## 1  
人間によるHTML直接編集は禁止

理由

- コピー事故
- CSS崩壊
- navズレ
- UI統一破壊

UI変更は **AIが完全ファイル生成**する。


---

## 2  
差分編集は禁止

必ず

完全ファイル

で更新する。

理由

- HTMLは差分ミスが発生しやすい
- indentation崩れ
- style破壊
- script破壊


---

## 3  
CSSはテーマのみ変更可能

変更可能ファイル

```

app/static/app.css

```

禁止

```

styleタグでのCSS追加
HTML個別CSS
ページ単位CSS

```

理由

UIはテーマ方式で統一する。


---

## 4  
Header / Nav / Footer は layout.js が生成する

```

app/static/common/layout.js

```

HTML側で

header
nav
footer

を個別に書いてはいけない。


---

## 5  
UIはテーマ方式で管理する

UI変更は必ず

```

app.css

```

から行う。


---

# レイアウト統一原則

全ページ共通

```

Home
Overlay
Sentiment
Digest
Prediction
Prediction History

```

レイアウト構造

```

Header
Hero
Panel
Grid
Footer

```

すべてのページで同一構造を維持する。


---

# ページHTMLの責務

HTMLは

**contentのみを書く**

例

```

hero
content
panel
list
timeline

```

レイアウトは

theme / layout

が管理する。


---

# UIトラブル時

優先確認

1  
app.css

2  
layout.js

3  
ページHTML


ページHTMLから疑うのは最後。


---

# AI作業ルール

## 完全ファイル保証ルール（UI特化）

UI生成時は以下を必ず守る

- 既存HTMLの行数より減少する生成は禁止
- HTMLの一部省略は禁止
- セクション欠落は禁止（header / hero / panel / script 等）
- placeholder化・簡略化は禁止

生成前ルール

- 必ずユーザーから対象ファイルを取得する
- 内容確認後に生成する

出力ルール

- 長文HTMLはダウンロード形式で提供する
- インライン出力での途中欠落を防ぐ

違反判定

以下はすべて生成失敗とみなす

- 行数が大幅に減少している
- セクションが消えている
- script / style が欠落している


UI修正時は必ず

```

完全ファイル

```

で出力する。


---

# このルールの目的

GenesisPrediction UI を

長期運用可能な構造

に保つため。


---

# 関連ドキュメント

```

docs/core/ui/ui_layout_standard.md
docs/core/ui/ui_design_system.md

```

## CSS分離ルール（HTML + CSS責務分離）

目的
UIの保守性・再利用性・可読性を向上させるため、
スタイル定義をHTMLから分離し、責務を明確にする。

原則

- 共通テーマは `app/static/app.css` に集約する
- ページ固有レイアウトは `app/static/<page>.css` に分離する
- HTMLは構造・DOM・JS読み込みのみを持つ
- HTML内 `<style>` の使用は禁止（例外なし）

新規実装ルール

- 新規ページは必ず `.html + .css` のペアで作成する
- ページ固有スタイルは必ず `<page>.css` に記述する

既存ページの扱い

- 既存ページは無理に一斉移行しない
- 大きく改修するタイミングで `.css` 分離を行う

禁止事項

- HTML内にスタイルを直書きすること
- UI側でレイアウト調整のための計算ロジックを書くこと

補足

UIは表示専用とする。
計算・判定・日付決定はすべて scripts / analysis 側で行う。

```
