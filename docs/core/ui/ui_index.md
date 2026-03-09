# UI Design Index
GenesisPrediction v2

Status: Active  
Location: docs/core/ui/  
Purpose: Provide a navigation and reading order for all UI design documents.

---

# 1. Purpose

この文書は **GenesisPrediction UI 設計ドキュメントの入口**である。

目的

- UI関連 docs の全体像を示す
- AI が読む順序を固定する
- 設計思想 / 部品 / レイアウト / コンポーネント仕様を整理する
- UI 改修時の参照ルートを明確にする

GenesisPrediction の UI docs は

```

思想
部品
骨格
共通コンポーネント

```

という **階層構造**で整理されている。

この文書はその **ナビゲーション**を提供する。

---

# 2. UI Design Layer Structure

UI設計は次の4層構造を持つ。

```

Layer 1
Design Philosophy

Layer 2
Component Catalog

Layer 3
Layout Standard

Layer 4
Component Standards

```

役割

| Layer | Role |
|-----|-----|
| Philosophy | UIの思想と原則 |
| Components | 再利用可能UI部品 |
| Layout | ページ骨格 |
| Component Standards | 個別UIコンポーネント仕様 |

---

# 3. Reading Order (AI / Developer)

UI作業時の **推奨読み順**

## Step 1 — Philosophy

```

ui_design_philosophy.md

```

理解すること

- GenesisPrediction UI の思想
- Clarity over decoration
- Research Dashboard concept
- 情報階層
- 長期安定性

これは **すべてのUI判断の基準**である。

---

## Step 2 — Component Catalog

```

ui_component_catalog.md

```

理解すること

- panel
- card
- hero
- status-shell
- timeline
- list-stack
- sparkline

つまり

**UI部品の辞書**

---

## Step 3 — Layout Standard

```

ui_layout_standard.md

```

理解すること

- ページ骨格
- section順序
- reading flow
- gridルール
- panel/card配置
- responsive原則

つまり

**ページの骨組み**

---

## Step 4 — Global Status Standards

```

global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
global_status_data_mapping.md

```

ここでは

**最重要共通コンポーネント**

Global Status を定義する。

内容

- コンポーネント思想
- HTML構造
- CSS構造
- データマッピング

---

# 4. UI Design Dependency Map

UI設計の依存関係

```

ui_design_philosophy
↓
ui_component_catalog
↓
ui_layout_standard
↓
global_status_*

```

意味

```

思想
↓
部品
↓
骨格
↓
個別コンポーネント

```

逆方向依存は禁止。

例

```

global_status が layout を変更する

```

これは禁止。

---

# 5. Relation to Active UI Docs

UI設計 docs は

```

docs/core/ui/

```

に存在する。

一方

**実装仕様**

は

```

docs/active/

```

に存在する。

対応関係

| Core UI | Active Spec |
|------|------|
| ui_design_philosophy | ui_system |
| ui_component_catalog | ui_system |
| ui_layout_standard | ui_system |
| global_status_* | ui_data_dependencies |

つまり

```

core/ui = 設計思想
active   = 実装仕様

```

---

# 6. When Updating UI

UI変更時は以下を確認する。

## Design change

更新対象

```

ui_design_philosophy.md

```

例

- UI思想変更
- dashboard concept変更

---

## New component

更新対象

```

ui_component_catalog.md

```

例

- 新しい reusable component

---

## Layout change

更新対象

```

ui_layout_standard.md

```

例

- ページ骨格変更
- section順序変更

---

## Global Status change

更新対象

```

global_status_*.md

```

例

- 新カード
- CSS変更
- DOM変更

---

# 7. Key Principle

GenesisPrediction UI は

```

Research Dashboard

```

である。

目的

```

世界の状況を理解する
危険信号を早く見つける
判断を助ける

```

そのため

```

Clarity over decoration

```

が最重要原則である。

---

# 8. Final Summary

UI docs 構造

```

docs/core/ui/

ui_index.md
ui_design_philosophy.md
ui_component_catalog.md
ui_layout_standard.md

global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
global_status_data_mapping.md

```

読む順序

```

ui_index
↓
ui_design_philosophy
↓
ui_component_catalog
↓
ui_layout_standard
↓
global_status_*

```

---

# End of Document
```
