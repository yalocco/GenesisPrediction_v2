相棒、いいところに気づきました。
まず質問の答えからいきます。

---

# ① thread_templates.md は情報源に入れる？

結論：

```text
YES
入れます
```

理由はシンプルです。

これは

```text
AI作業プロトコル
```

だからです。

つまりあなたの Repository Memory の分類でいうと

```
Development Rules
```

に属します。

---

# ② Repository Memoryの位置

ここに入れるのが一番自然です。

```text
## Development Rules

docs/working_agreement.md
docs/chat_operating_rules.md
docs/gui_phase2_working_rules.md
docs/thread_templates.md   ← NEW
```

これで AI は

```
作業ルール
↓
スレ運用
```

まで理解できます。

---

# ③ thread_templates.md の役割

これは **AIスレ運用マニュアル**です。

内容はこの2つ。

```
新スレ開始テンプレ
スレ終了テンプレ
```

つまり

```
AIスレ lifecycle
```

を固定します。

---

# ④ 完全ファイル

これをそのまま

```
docs/thread_templates.md
```

として保存してください。

---

# docs/thread_templates.md（完全ファイル）

```md
# Thread Templates
GenesisPrediction v2

Status: Active  
Purpose: AI作業スレの開始と終了テンプレート  
Last Updated: 2026-03-06

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

AI作業スレの

```

開始
終了

```

テンプレートを定義する。

目的

- AIがプロジェクト状態を正しく理解する
- スレ開始時の説明コストを減らす
- スレ終了時の状態を明確にする
- 作業履歴を読みやすくする

---

# 1. Thread Start Template

新しいスレを開始する際は

```

docs/ai_thread_start_template.md

```

を使用する。

このテンプレートは

AIが以下を理解するためのもの

```

Repository Memory
Architecture
Rules
Current Task
Next Action

```

---

# 2. Thread End Template

作業スレ終了時は

以下を記録する。

---

## Template

```

【このスレ完了】

GenesisPrediction v2

作業内容
（例）
Sentiment UI 調整

commit
（commit id）

状態

repo clean
origin/main 同期済み

備考
（必要なら）

次スレ予定
（例）

Sentiment分類有効化
positive / negative / neutral / mixed

```

---

# 3. Thread Lifecycle

GenesisPrediction v2 の AI作業スレは

以下の流れで運用する。

```

新スレ開始
↓
作業
↓
commit
↓
push
↓
repo clean
↓
スレ終了テンプレ

```

---

# 4. Design Principle

AIスレは

```

1スレ = 1テーマ

```

を基本とする。

理由

- AIのコンテキストを整理する
- デバッグしやすくする
- 履歴を読みやすくする

---

# 5. When to Create New Thread

以下の場合は新スレを作成する。

```

スレが重くなった
テーマが変わった
大きなUI作業
ログが増えた

```

---

# 6. Recommended Thread Naming

スレ名は

```

テーマ + フェーズ

```

で作成する。

例

```

Sentiment分類有効化
GUI安定化フェーズ2
FX判断エンジン統一
Morning Ritual 自然治癒設計

```

---

# 7. AI Collaboration Principle

GenesisPrediction は

```

Human + AI

```

の共同研究プロジェクトである。

Human

```

目的
判断
倫理

```

AI

```

分析
設計補助
コード生成

```

---

END OF DOCUMENT
```
