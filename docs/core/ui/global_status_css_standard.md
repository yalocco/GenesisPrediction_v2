# Global Status CSS Standard
GenesisPrediction v2

Version: 1.0  
Status: Active  
Location: docs/core/ui/

---

# 1. Purpose

この文書は  
GenesisPrediction UI における **Global Status の CSS 実装標準**を定義する。

対象

- layout
- card appearance
- typography
- spacing
- responsive
- state styling

目的

- UI の見た目の統一
- ページごとの CSS 差分を防ぐ
- Global Status を **完全な共通UIコンポーネント**として固定する

---

# 2. Scope

対象ページ

- Home
- Overlay
- Sentiment
- Digest
- Prediction
- Prediction History

すべてのページで

```

同一 CSS
同一 layout
同一 card design

```

を使用する。

ページ別 CSS override は禁止。

---

# 3. CSS Responsibility

Global Status のスタイルは **app.css のみ**に定義する。

定義場所

```

app/static/app.css

```

禁止

```

page-specific CSS
inline style
JS style manipulation

```

許可

```

.global-status-panel
.global-status
.status-card
.status-label
.status-value
.status-sub

```

---

# 4. Layout Structure

Global Status の基本レイアウト

```

Panel
└ Global Status Grid
├ Card 1
├ Card 2
├ Card 3
├ Card 4
└ Card 5

```

Grid layout

```

display: grid
grid-template-columns: repeat(5, 1fr)
gap: 12px

````

カードは **5列固定**。

折り返しは禁止。

---

# 5. Standard Layout CSS

標準レイアウト

```css
.global-status {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
````

カード

```css
.status-card {
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--panel-bg);
}
```

---

# 6. Typography Rules

label

```css
.status-label {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.75;
}
```

value

```css
.status-value {
  font-size: 22px;
  font-weight: 700;
  margin-top: 4px;
}
```

sub

```css
.status-sub {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.7;
}
```

---

# 7. Spacing Rules

カード内部 spacing

```
label
↓ 4px
value
↓ 4px
sub
```

padding

```
14px 16px
```

gap

```
12px
```

---

# 8. Color Responsibility

色は CSS Variables で制御する。

例

```css
--panel-bg
--border-color
--text-muted
```

Global Status 専用カラーは作らない。

理由

```
テーマ変更
ダークモード
ブランド統一
```

に対応するため。

---

# 9. State Styling

state は HTML attribute で表す。

例

```
data-state="ready"
data-state="warn"
data-state="empty"
data-state="unavailable"
data-state="loading"
```

CSS

```css
.status-card[data-state="warn"] {
  border-color: #e6b800;
}

.status-card[data-state="empty"] {
  opacity: 0.7;
}

.status-card[data-state="unavailable"] {
  opacity: 0.5;
}

.status-card[data-state="loading"] {
  opacity: 0.6;
}
```

JS が style を直接変更してはならない。

---

# 10. Responsive Rules

PC

```
5 columns
```

Tablet

```
3 columns
```

Mobile

```
2 columns
```

CSS

```css
@media (max-width: 900px) {
  .global-status {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 600px) {
  .global-status {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

注意

```
HTML構造は変更しない
カード数は変更しない
```

---

# 11. Visual Consistency Rules

次の要素は **全ページ共通**とする。

```
card border
background
padding
font sizes
gap
grid layout
```

ページごとに見た目を変えてはいけない。

---

# 12. Forbidden Styling

禁止事項

```
inline style
page-specific override
JS style manipulation
カード数変更
grid構造変更
```

Global Status は **装飾ではなくシステムUI**である。

---

# 13. Accessibility

最低限のアクセシビリティ

```
十分な文字サイズ
色だけで意味を伝えない
sub text を必ず表示
```

Global Status は

```
色無しでも読めるUI
```

であること。

---

# 14. Performance Rule

Global Status は

```
CSS only layout
JS minimal update
```

とする。

理由

```
全ページ共通UIのため
描画コストを抑える
```

---

# 15. Relation to Other Standards

Global Status は次の標準とセットで使用する。

```
global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
```

3つで

```
Component
HTML
CSS
```

が完全定義される。

---

# 16. Definition of Done

CSS標準が適用された状態

```
全ページで同一見た目
5カード横並び
state表示が統一
inline style無し
page-specific override無し
```

これを満たすと **Global Status UI 完成**とする。

---

# 17. Version History

v1.0
Initial CSS standard for Global Status

```
