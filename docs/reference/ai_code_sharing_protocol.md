# GenesisPrediction

# AIコード共有プロトコル v1

目的

* 長文コード共有を **安全・確実・高速**にする
* コピペ事故を防ぐ
* ChatGPTのストリームエラーを回避する
* Git運用を壊さない

対象

```
HTML
CSS
JS
Python
PowerShell
.md
```

特に

```
500行以上のファイル
```

---

# 共有優先順位

AIは **次の順序でコードを共有する**

```
① ダウンロードファイル
↓
② ZIP
↓
③ canvas
↓
④ 最終手段：長文
```

---

# ① ダウンロードファイル（最優先）

形式

```
prediction.html
overlay.html
scenario_engine.py
```

使用条件

```
通常のコード共有
```

メリット

* コピペ事故ゼロ
* 改行崩れない
* VSCodeで即上書き
* Git diff正常

手順

```
AI → ファイル生成
↓
ユーザー保存
↓
VSCode上書き
↓
git commit
```

---

# ② ZIP（ダウンロード失敗対策）

使用条件

```
ダウンロードが反応しない
ブラウザ不具合
```

形式

```
prediction_fix.zip
 └ prediction.html
```

メリット

* ChatGPTダウンロード不具合回避
* 長文安定

---

# ③ canvas（長文閲覧用）

使用条件

```
HTML 1000行以上
構造確認
レビュー
```

目的

```
閲覧
確認
レビュー
```

注意

canvasは

```
保存用途ではない
```

---

# ④ 最終手段：長文

使用条件

```
①②③が使えない場合
```

形式

````
```html
完全ファイル
````

```

注意

```

必ず完全ファイル
差分禁止

```

---

# ファイル提示ルール

AIは必ず **ファイル名を明示する**

例

```

File:
app/static/prediction.html

```

これにより

```

上書き事故
index.html誤爆

```

を防ぐ。

---

# 完全ファイルルール

GenesisPredictionでは

```

差分禁止

```

必ず

```

完全ファイル全文

```

を提示する。

---

# 大型ファイル基準

次の場合は **canvasまたはファイル**

```

HTML > 500行
JS > 400行
Python > 400行

```

---

# Git運用ルール

ユーザー側手順

```

保存
↓
VSCode上書き
↓
git status
↓
git add
↓
git commit
↓
git push

```

---

# AI禁止事項

AIは次を行ってはならない

```

差分提示
部分コード
行番号省略

```

必ず

```

完全ファイル

```

---

# まとめ

GenesisPrediction コード共有順序

```

① ダウンロード
② ZIP
③ canvas
④ 長文

```
