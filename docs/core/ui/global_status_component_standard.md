# Global Status Component Standard
GenesisPrediction v2

Version: 1.0  
Status: Active  
Location: docs/core/ui/

---

# 1. Purpose

Global Status は GenesisPrediction UI の **最重要共通コンポーネント**である。

目的：

- 全ページで **現在のシステム状態を一目で把握**できるようにする
- ページごとの UI 実装差異をなくす
- 判断系 UI（Prediction / Overlay / Sentiment）への **入口情報を統一**する
- 将来 UI を拡張しても **表示構造を固定する**

Global Status は **全ページ共通 UI** とする。

---

# 2. Target Pages

Global Status を表示するページ

- Home
- Overlay
- Sentiment
- Digest
- Prediction
- Prediction History

これらのページは **同一構造の Global Status を使用する。**

---

# 3. Component Structure

Global Status は **5カード固定構造**とする。

```

[ CARD 1 ] [ CARD 2 ] [ CARD 3 ] [ CARD 4 ] [ CARD 5 ]

```

各カードは次の構造を持つ。

```

Label
Value
Sub text

```

例

```

Date
2026-03-09
UTC

```

構造

```

.card
├ label
├ value
└ sub

```

---

# 4. Layout Rules

レイアウト規則

- 横並び **5カード固定**
- 折り返し禁止
- ページ幅いっぱいに配置
- カード幅は **均等分割**

```

display: grid
grid-template-columns: repeat(5, 1fr)

```

モバイル時のみ

```

grid-template-columns: repeat(2, 1fr)

```

---

# 5. Data Source Rules

Global Status は **ViewModel JSON を読み取る。**

主な情報源

```

analysis/viewmodel/
analysis/daily_summary/
analysis/prediction/
analysis/health/

```

ページごとに **必要な JSON を選択する。**

ただし

**Global Status 表示構造は変えない。**

---

# 6. Loading State

データ読み込み中

表示

```

—
loading

```

例

```

Prediction
—
loading

```

---

# 7. Empty State

データが存在しない場合

表示

```

—
no data

```

---

# 8. Unavailable State

JSON取得失敗 / API失敗

表示

```

—
unavailable

```

---

# 9. CSS Responsibility

Global Status のスタイルは **app.css にのみ定義する。**

禁止

- ページ個別 CSS
- inline style
- script での style 操作

許可

```

.global-status
.card
.label
.value
.sub

```

---

# 10. UI Consistency Rules

次の要素は **すべてのページで同一にする**

- card layout
- font size
- spacing
- border
- background
- color

ページごとに **見た目を変えてはいけない。**

---

# 11. Forbidden Changes

禁止事項

- カード数変更
- ページごとの card layout 差分
- CSS のページ個別 override
- inline style
- DOM 構造変更

Global Status は **システム共通 UI である。**

---

# 12. Future Extension

将来追加可能

例

- System Health
- Prediction Confidence
- FX Risk State

ただし

**カード数変更は禁止。**

追加する場合は

```

既存カード置き換え

```

で対応する。

---

# 13. Design Philosophy

Global Status は

**装飾ではなく判断のためのUI**

である。

重要原則

- 一目で状況がわかる
- UIを壊さない
- ページ間差異を作らない
- 読みやすさ優先

---

# 14. Version History

v1.0  
Initial standard definition
```
