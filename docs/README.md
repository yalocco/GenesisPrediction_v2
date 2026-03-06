# Docs Guide (GenesisPrediction v2)

このディレクトリは **GenesisPrediction v2 の「人間のための記憶・運用台本」** です。
コードや自動処理とは役割を分け、

**「どう使うか」「どう考えるか」「何を信頼するか」**

を固定します。

---

# 🤖 AI Bootstrap（最初に読む）

新しい AI / 新しいスレッド / 新しいPC で作業する場合は
**必ず最初に以下を読む。**

```
docs/ai_bootstrap_prompt.md
```

このファイルは

* AI初期化
* Repository Memoryの読み込み
* 作業ルールの適用

を行う **AI起動プロンプト**です。

---

# 📘 Human Operation Docs（人間運用ドキュメント）

人間が **毎日の運用・観測・思考整理** に使うドキュメント。

---

## runbook_morning.md（最重要）

毎日の正式運用手順（凍結）。

内容

* 朝の儀式（Morning Ritual）
* GUI / CLI の実行順
* 運用禁止事項（事故防止）

基本フロー

```
git pull
↓
run_daily_with_publish.ps1
↓
FX lane
↓
Data Health
↓
GUI確認
```

迷ったら **まず runbook_morning.md を読む。**

---

## observation.md

日付ごとの観測ログ。

内容

* 自動生成ログ
* 人間の1行所感

目的

```
観測
↓
仮説
↓
判断
```

の履歴を残す。

---

## gui_f1_panel_spec.md

GUI F-1パネル設計書。

目的

* GUI実装前の合意
* UI仕様の凍結

GUIを触る前に読む。

---

## assumptions.md

分析の前提条件。

内容

* 世界観
* 分析の前提
* 暗黙ルール

---

## diff_schema.md

diff / daily_summary の構造説明。

目的

* データ理解
* JSON構造理解

---

## fragile_points.md

壊れやすい箇所のメモ。

内容

* 注意点
* 触ると壊れる箇所

---

# 🧭 運用原則（要約）

```
.md は人間のために書く
自動生成はヒントまで
判断は人間が確定
迷ったら観測へ戻る
```

---

# 📝 更新ルール

```
小さく書く（1行でも良い）
毎日書く必要はない
書かない日があっても問題なし
```

---

# 🗄 Data Management

```
data/ は Git 管理しない
PC間同期は Syncthing
```

運用ルール

```
docs/data_sync_rule.md
```

---

# 🤖 AI Development Docs（Repository Memory）

GenesisPrediction v2 は
**AI共同開発プロジェクト**です。

Chat の記憶に依存せず

```
docs/
```

に **設計知識を保存する仕組み**を持ちます。

---

## repo_map.md

リポジトリ構造の地図。

内容

```
scripts
analysis
app/static
```

の責務分離。

---

## repo_architecture.md

GenesisPrediction の **三層構造**。

```
Chat Memory
↓
Repository Memory
↓
Project Knowledge
```

---

## project_status.md

プロジェクトの現在地。

内容

* 現在のUI
* pipeline状態
* stable tags
* 次の作業

---

## pipeline_system.md

パイプライン構造。

基本フロー

```
Morning Ritual
↓
Analyzer
↓
Sentiment
↓
Digest
↓
Overlay
↓
Health
```

---

## ui_system.md

UI構造の仕様書。

対象ページ

```
Home
Overlay
Sentiment
Digest
```

内容

* HTML構造
* JSON依存
* UI責務
* CSS構造

---

## chat_operating_rules.md

AI共同開発ルール。

基本原則

```
1ターン = 1作業
差分修正禁止
完全ファイル提示
```

---

## genesis_brain.md

GenesisPrediction の設計思想。

内容

```
Single Source of Truth
Pipeline思想
分析哲学
AI共同開発構造
```

---

# 🧠 GenesisPrediction Knowledge Architecture

GenesisPrediction v2 は
以下の **三層構造**で知識を管理する。

```
Chat Memory
↓
Repository Memory (docs)
↓
Project Knowledge
```

---

## Chat Memory

AIとの会話履歴

内容

* 設計議論
* 問題解決
* 実験
* 仮説

特徴

* 一時的
* スレ変更で消える

---

## Repository Memory

リポジトリ内の設計知識。

場所

```
docs/
```

内容

* UI構造
* Pipeline構造
* AI作業ルール
* 設計思想

---

## Project Knowledge

実際のシステム。

```
scripts/
analysis/
app/static/
data/
```

---

# 🧩 この構造のメリット

この構造により

```
AI変更
PC変更
スレ変更
```

が起きても

* 開発継続可能
* 構造理解を即復元
* 手順再説明不要

となる。

---

GenesisPrediction v2 は
**AIと人間の共同開発プロジェクト**である。
