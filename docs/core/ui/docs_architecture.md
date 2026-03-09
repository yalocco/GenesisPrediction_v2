# Docs Architecture
GenesisPrediction v2

Status: Active  
Purpose: docs/ の構造、役割、AI の読み順を固定する  
Last Updated: 2026-03-09  
Location: docs/core/

---

# 0. Purpose

この文書は

**GenesisPrediction v2 の docs/ 構造そのものを定義する**

ための設計文書である。

目的

- docs の役割を明確にする
- AI がどの docs をどう読むべきかを固定する
- 設計文書と補助文書を混同しないようにする
- Repository Memory の入口を 1 枚で示す
- 新しい AI / 新しい PC / 新しい環境でも同じ理解を再現できるようにする

GenesisPrediction では

```text
docs = Repository Memory
````

である。

docs は単なるメモ置き場ではない。
docs は

* 設計思想
* 構造定義
* 実装仕様
* 履歴
* 補助知識

を分離して保存するための **知識アーキテクチャ** である。

---

# 1. Core Principle

docs 設計の最重要原則はこれである。

```text
設計の真実と作業補助を混ぜない
```

GenesisPrediction は長期研究プロジェクトであり、
AI が docs を読む前提で開発される。

そのため docs は

```text
Core Design
Current Spec
Reference
History
Obsolete
```

を分離して管理する。

重要:

```text
docs は AI の思考 OS
```

である。

---

# 2. Relation to Repository Structure

GenesisPrediction 全体の責務は次のように分離される。

```text
scripts = 生成
data = 素材
analysis = 真実
app = 表示
docs = 設計
```

docs は Repository Memory として、

* repo 構造の理解
* システムの思想
* UI の骨格
* Prediction の設計
* 変更履歴と判断理由

を保存する。

重要原則:

```text
analysis = Single Source of Truth
docs = Single Source of Design Intent
```

つまり

* 実行時の真実は analysis
* 設計上の真実は docs

である。

---

# 3. Docs Top Structure

docs は以下の構造に整理する。

```text
docs/

core/
active/
reference/
archive/
obsolete/
ADR/
runbook/
```

意味

## core

最重要設計思想
長期的に維持される原則
AI が最初に読むべき層

## active

現行システム仕様
現在の実装に直接対応する層

## reference

補助資料
作業補助
人間や AI の運用参考

## archive

過去設計・履歴保存
現在の正式仕様ではないが削除しない

## obsolete

完全廃止文書
現在は使わない

## ADR

Architecture Decision Record
重要判断の履歴

## runbook

運用手順
日次運用・トラブル対応・作業手順

---

# 4. Meaning of Each Layer

## 4.1 core

core は **削除禁止** の設計思想層である。

ここには

* プロジェクトの核心思想
* 長期的に維持される原則
* 設計判断の土台
* UI / Prediction / Memory の上位原則

を置く。

例

```text
genesis_brain.md
decision_log.md
system_history.md
project_status.md
prediction_layer_design_principles.md
docs_architecture.md
```

特徴

* 実装変更より長生きする
* AI がまず理解すべき
* “なぜそう設計するのか” を持つ

---

## 4.2 core/ui

core/ui は **UI の設計中核** である。

ここには

* UI思想
* UI部品
* UI骨格
* 共通コンポーネント標準

を置く。

例

```text
ui_design_philosophy.md
ui_component_catalog.md
ui_layout_standard.md

global_status_component_standard.md
global_status_html_standard.md
global_status_css_standard.md
global_status_data_mapping.md
```

特徴

* UI 改修時の基準
* 画面ごとの差分暴走を防ぐ
* AI の勝手な構造変更を止める

---

## 4.3 active

active は **現行実装仕様** である。

ここには

* 現在の repo 構造
* pipeline 構造
* analysis schema
* UI data dependency
* prediction architecture
* roadmap

など、実装と同期する仕様文書を置く。

例

```text
genesis_system_map.md
repo_map.md
pipeline_system.md
analysis_data_schema.md
ui_system.md
ui_data_dependencies.md
prediction_architecture.md
genesis_prediction_roadmap.md
```

特徴

* 実装変更時に同期更新が必要
* “今のシステムはどうなっているか” を示す
* core より変更頻度が高い

---

## 4.4 reference

reference は **補助文書** である。

ここには

* AI起動補助
* 作業ルール
* quick context
* debug の参考
* 運用ヒント

などを置く。

特徴

* 便利だが設計の真実ではない
* AI 情報源に常時入れない判断があり得る
* 人間向け導入資料として有効

重要原則

```text
reference は仕様ではない
```

---

## 4.5 archive

archive は **過去設計の保管庫** である。

特徴

* 歴史資料
* 旧設計
* 判断経緯の確認に使う
* 現行仕様としては読まない

重要原則

```text
archive は読む前に active / core を先に確認する
```

---

## 4.6 obsolete

obsolete は **完全廃止文書** である。

特徴

* 現在の設計では使わない
* 参照禁止ではないが通常は読まない
* 将来削除候補

---

## 4.7 ADR

ADR は **重要判断の記録** である。

用途

* 変更理由の保存
* 判断再発明の防止
* AI が「なぜこの設計か」を理解する補助

ADR は core / active を補助するが、
仕様そのものの代替ではない。

---

## 4.8 runbook

runbook は **運用手順** である。

用途

* Morning Ritual
* 日次確認
* トラブル対応
* 公開手順
* 環境セットアップ

重要原則

```text
runbook = 運用
spec = 設計
```

混同しない。

---

# 5. AI Reading Order

AI は docs を以下の順で読む。

## Phase 1: Project Philosophy

まず理解すべきもの

```text
docs/core/genesis_brain.md
docs/core/decision_log.md
docs/core/system_history.md
docs/core/project_status.md
```

目的

* このプロジェクトは何か
* 何を目指しているか
* 何を大事にしているか
* 最近どんな判断があったか

---

## Phase 2: Repository and Runtime Structure

次に読むもの

```text
docs/active/genesis_system_map.md
docs/active/repo_map.md
docs/active/pipeline_system.md
docs/active/analysis_data_schema.md
```

目的

* repo の責務分離
* pipeline の流れ
* analysis の構造
* 真実の所在

---

## Phase 3: Prediction Structure

次に読むもの

```text
docs/core/prediction_layer_design_principles.md
docs/active/prediction_architecture.md
docs/active/genesis_prediction_roadmap.md
```

目的

* Prediction を主役にしない原則
* Observation → Trend → Signal → Scenario → Prediction
* 長期進化方向

---

## Phase 4: UI Structure

UI 作業時に読むもの

```text
docs/active/ui_system.md
docs/active/ui_data_dependencies.md

docs/core/ui/ui_design_philosophy.md
docs/core/ui/ui_component_catalog.md
docs/core/ui/ui_layout_standard.md

docs/core/ui/global_status_component_standard.md
docs/core/ui/global_status_html_standard.md
docs/core/ui/global_status_css_standard.md
docs/core/ui/global_status_data_mapping.md
```

目的

* UI の責務
* UI のデータ依存
* UI の思想
* UI の部品
* UI の骨格
* 共通コンポーネント標準

---

## Phase 5: Operational Support

必要時のみ読むもの

```text
docs/runbook/*
docs/reference/*
docs/ADR/*
```

目的

* 実行手順
* トラブルシュート
* 補助説明
* 過去判断の確認

---

# 6. Source Priority Rule

AI が複数文書を読んだとき、優先順位はこうする。

```text
1. core
2. active
3. ADR
4. runbook
5. reference
6. archive
7. obsolete
```

意味

* core が思想の基準
* active が現行実装の基準
* ADR は判断理由の補助
* runbook は運用補助
* reference は作業補助
* archive / obsolete は通常使わない

重要原則

```text
迷ったら core → active を正とする
```

---

# 7. Information Source Rule

AI 情報源に入れる対象は原則として次の層に限る。

```text
core
active
```

条件付きで参照してよい層

```text
ADR
runbook
```

通常は情報源から外す候補

```text
reference
archive
obsolete
```

理由

* 仕様と補助文書を混ぜないため
* AI 誤読を防ぐため
* Single Source of Design Intent を守るため

---

# 8. Document Classification Rule

新しい md を追加する時は、必ず次で判定する。

## core に置くもの

* 長期原則
* 設計思想
* 基本方針
* 他文書の上位ルール

## active に置くもの

* 現行仕様
* 現在の runtime 構造
* 現行ファイル依存
* 実装追従が必要な定義

## reference に置くもの

* quick context
* bootstrap
* 会話運用
* 作業の補助説明

## runbook に置くもの

* 実行手順
* 復旧手順
* 環境手順

## archive に置くもの

* 旧版仕様
* 過去メモ
* 歴史保全

## obsolete に置くもの

* 廃止済み設計
* 置換済み文書

---

# 9. Update Rule

docs を更新した時は、次を守る。

## 9.1 core 変更時

* 設計思想の変更である
* 影響範囲を確認する
* 必要なら active 側も整合させる

## 9.2 active 変更時

* 現行実装に同期する
* 実装変更と同時に更新する
* schema / dependency / source の変化を反映する

## 9.3 UI 標準変更時

UI 変更内容に応じて以下を更新する。

```text
思想変更       → ui_design_philosophy.md
部品変更       → ui_component_catalog.md
骨格変更       → ui_layout_standard.md
Global Status  → global_status_*.md
依存変更       → ui_data_dependencies.md
```

## 9.4 パス変更時

ファイルの保存場所が変わった場合

* docs 内の参照を見直す
* 情報源は旧パスを外し、新パスで入れ直す
* 旧版が残るなら archive / obsolete を検討する

---

# 10. Design Intent

docs 設計の意図は単純である。

```text
AI が毎回 repo を探検しなくていい状態を作る
```

つまり

* 新しい AI
* 新しい会話
* 新しい PC
* Open-WebUI / ChatGPT / local LLM

のどれでも、

```text
docs を読めば同じ理解に到達できる
```

状態を目指す。

---

# 11. Final Summary

GenesisPrediction の docs は

```text
core      = 長期設計思想
active    = 現行仕様
reference = 補助資料
archive   = 履歴保存
obsolete  = 廃止資料
ADR       = 判断履歴
runbook   = 運用手順
```

で構成される。

AI は

```text
core → active → 必要時に ADR / runbook
```

の順で読む。

最重要原則

```text
analysis = Single Source of Truth
docs = Single Source of Design Intent
```

である。

---

# 12. Version History

v1.0
Initial docs architecture definition for Repository Memory

```
