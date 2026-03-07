# docs/ai_startup_protocol.md

````md
# AI Startup Protocol (GenesisPrediction v2)

Version: 1.0
Status: Active
Last Updated: 2026-03-06

---

# 0. 目的

本ドキュメントは  
GenesisPrediction v2 において **新しいAIをどう起動するか** を固定するための公式手順である。

目的：

- 新しいスレでも同じ前提で開始する
- AIに毎回構造説明をやり直さない
- Chat Memory ではなく Repository Memory を優先させる
- AIの初動ミスを防ぐ

---

# 1. 基本原則

GenesisPrediction v2 では  
AIは **Chat Memory ではなく Repository Memory（docs）を優先**する。

知識構造：

Chat Memory  
↓
Repository Memory  
↓
Project Knowledge  

AIは起動時に必ず

- ai_bootstrap_prompt.md
- Repository Memory
- project_status.md

を基準に動く。

---

# 2. 起動時に最初に読むファイル

新しいAIは、まず以下を読む。

## 最優先

- `docs/ai_bootstrap_prompt.md`

## 主要知識

- `docs/repo_map.md`
- `docs/repo_architecture.md`
- `docs/project_status.md`
- `docs/pipeline_system.md`
- `docs/ui_system.md`
- `docs/genesis_brain.md`
- `docs/chat_operating_rules.md`

## 必要時に読む

- `docs/runbook_morning.md`
- `docs/working_agreement.md`
- `docs/gui_phase2_working_rules.md`

---

# 3. 起動手順（標準）

## Step 1

AIに以下を与える。

```text
docs/ai_bootstrap_prompt.md を前提知識として扱ってください。
````

---

## Step 2

AIが Repository Memory を参照することを確認する。

最低限、以下を前提にしていること。

* `repo_map.md`
* `project_status.md`
* `pipeline_system.md`
* `ui_system.md`

---

## Step 3

そのスレでの **今回の1作業** を与える。

例：

* Sentiment分類の有効化を続ける
* Digest UI の依存JSONを確定する
* Morning Ritual のwarn原因を切り分ける

---

# 4. 起動後のAIルール

AIは必ず以下を守る。

* 1ターン = 1作業
* 差分修正禁止
* 完全ファイル提示
* 長大ファイルはダウンロード運用
* UIは analysis を読むだけ
* analysis を手動で真実化しない

---

# 5. 問題発生時の判断順

## UIが壊れた

1. analysis を確認
2. analysis が正しい → GUI問題
3. analysis が壊れている → scripts問題

## 数値が出ない

1. analysis を確認
2. scripts の生成状況を見る
3. data を確認する

## パイプライン停止

* `scripts/` を確認する
* `runbook_morning.md` を参照する

---

# 6. AIごとの使い方

## 6.1 ChatGPT 新スレ

新スレ1投稿目に、以下のどちらかを貼る。

### 標準

`docs/ai_bootstrap_prompt.md` の全文

### 短縮

```text
GenesisPrediction v2 の作業です。
docs/ai_bootstrap_prompt.md を前提に進めてください。
今回の作業は project_status.md の Next Action を基準にします。
```

---

## 6.2 Open-WebUI / ローカルLLM

セッション開始時に以下を与える。

```text
GenesisPrediction v2 の開発を開始します。
まず docs/ai_bootstrap_prompt.md を読んで、Repository Memory を優先してください。
```

必要なら Knowledge Source として以下を登録する。

* `docs/repo_map.md`
* `docs/repo_architecture.md`
* `docs/project_status.md`
* `docs/pipeline_system.md`
* `docs/ui_system.md`
* `docs/genesis_brain.md`
* `docs/chat_operating_rules.md`

---

# 7. 起動成功の条件

以下をAIが理解していれば、起動成功とする。

* `analysis/` が Runtime SST
* `scripts/` が生成
* `app/static/` が表示
* 今回の作業が何か
* 完全ファイル運用ルール
* 1ターン = 1作業

---

# 8. 禁止事項

* Chat履歴だけを前提に作業する
* docs を読まずに構造を推測する
* UI側で再計算を始める
* 差分パッチを出す
* 1ターンで複数案件を混ぜる

---

# 9. 結論

GenesisPrediction v2 のAIは

AI Bootstrap
↓
Repository Memory
↓
Project Knowledge

の順で起動する。

この順序を守ることで、
AIは毎回 **同じ構造理解から安全に作業開始**できる。

---

END OF DOCUMENT

