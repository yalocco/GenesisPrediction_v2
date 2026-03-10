# Repository Architecture (GenesisPrediction v2)

Version: 1.0
Status: Active
Last Updated: 2026-03-06

---

# 0. 目的

本ドキュメントは
GenesisPrediction v2 の **設計構造の全体図** を固定する。

この文書を読むことで

* AI
* 新しいスレッド
* 将来の自分

が **5秒でプロジェクト構造を理解できる状態**を作る。

---

# 1. GenesisPrediction の三層構造

GenesisPrediction v2 は
以下の **3層構造**で知識を管理する。

```
Chat Memory
↓
Repository Memory
↓
Project Knowledge
```

---

## 1.1 Chat Memory

AIとの会話履歴

内容

* 設計議論
* 問題解決
* 実験
* 仮説

特徴

* 一時的
* スレが変わると消える

---

## 1.2 Repository Memory

リポジトリ内の **docs/** に保存された設計知識。

```
docs/
```

役割

* AIが構造を理解するための知識
* プロジェクト思想
* 作業ルール
* システム構造

---

## 1.3 Project Knowledge

実際のシステム。

```
scripts/
data/
analysis/
app/static/
```

ここが **実行される世界**。

---

# 2. Repository Memory（docs）の役割

docs は

```
人間運用
+
AI設計
```

の **二階建て構造**で構成される。

---

## 2.1 Human Operation Docs

人間が運用するための知識。

例

```
runbook_morning.md
observation.md
fragile_points.md
assumptions.md
```

目的

* 運用の再現性
* 観測ログ
* 注意点共有

---

## 2.2 AI Design Docs

AIがプロジェクト構造を理解するための知識。

```
ui_system.md
pipeline_system.md
chat_operating_rules.md
genesis_brain.md
project_status.md
repo_architecture.md
```

目的

* AIが構造を忘れない
* スレ変更時の再説明不要
* 設計思想の固定

---

# 3. Project Knowledge（実システム）

## 3.1 scripts/

役割

```
SST生成装置
```

例

```
run_daily_with_publish.ps1
run_daily_fx_rates.ps1
run_daily_fx_overlay.ps1
build_data_health.py
```

---

## 3.2 data/

役割

```
素材
```

特徴

* Git管理しない
* 再生成可能

---

## 3.3 analysis/

役割

```
Single Source of Truth
```

GenesisPrediction v2 の **唯一の真実**。

GUIは

```
analysis/
```

のみを読む。

---

## 3.4 app/static/

役割

```
表示UI
```

内容

```
index.html
overlay.html
sentiment.html
digest.html
```

特徴

* analysis を読むだけ
* 再計算しない

---

# 4. パイプライン構造

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

詳細は

```
docs/pipeline_system.md
```

を参照。

---

# 5. UI構造

現在のページ

```
Home
Overlay
Sentiment
Digest
```

詳細は

```
docs/ui_system.md
```

を参照。

---

# 6. 作業ルール

AI共同開発ルール

```
1ターン = 1作業
差分修正禁止
完全ファイル提示
```

詳細

```
docs/chat_operating_rules.md
```

---

# 7. 設計思想

GenesisPrediction v2 の思想。

```
Single Source of Truth
責務分離
再現性優先
```

詳細

```
docs/genesis_brain.md
```

---

# 8. 現在地

現在のプロジェクト状態は

```
docs/project_status.md
```

に保存される。

---

# 9. 結論

GenesisPrediction v2 は

```
Chat Memory
↓
Repository Memory
↓
Project Knowledge
```

の三層構造で動く
**AI共同開発システム**である。

---

END OF DOCUMENT
