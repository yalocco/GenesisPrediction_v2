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
```
