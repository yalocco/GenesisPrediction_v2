了解しました 👍
そして先に **重要な答え**から言います。

**`task_board.md` は 情報源に入れません。**

理由：

```text
これは「作業管理」
AI知識ではない
```

つまり

```text
repo_map.md → AI知識
pipeline_system.md → AI知識
task_board.md → 作業メモ
```

です。

---

# 作るファイル

```text
docs/task_board.md
```

役割

```text
今やっている作業
次にやる作業
完了した作業
```

を整理します。

これは **AI作業を迷わせないためのボード**です。

---

# docs/task_board.md（完全ファイル）

そのまま保存してください。

```md
# GenesisPrediction v2 Task Board

Status: Active  
Last Updated: 2026-03-06

---

# 目的

このファイルは  
GenesisPrediction v2 の **作業管理ボード**である。

目的：

- AI作業を迷わせない
- 現在の作業位置を明確にする
- 次にやる作業を固定する
- 長期開発の整理

---

# 現在の状態

## Repository Memory

完成

```

docs/
Repository Knowledge System

```

含まれるもの

- AI bootstrap
- Repository architecture
- Pipeline design
- UI design
- AI rules
- ADR
- AI startup protocol

---

## UI

現在のページ

```

Home
Overlay
Sentiment
Digest

```

Digest UI は安定版完成。

---

## Pipeline

現在の構造

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

Morning Ritual は安定動作。

---

# 現在の作業

Sentiment分類 有効化

```

positive
negative
neutral
mixed

```

現在

```

unknown が多い

```

原因

```

Sentiment join mismatch

```

---

# 次の作業

## 1

Sentiment分類を有効化

目標

```

unknown を減らす

```

---

## 2

Digest KPI を正常化

表示

```

positive
negative
neutral
mixed

```

---

## 3

Sentiment Trend 改良

予定

```

3軸グラフ

```

---

# 次フェーズ

Phase 2

```

FX overlay 判断エンジン統一

```

対象

```

JPY-THB
USD-JPY
USD-THB

```

---

# 将来フェーズ

Phase 3

Prediction Engine

```

signals
scenarios
predictions

```

---

# 完了した主要作業

## Repository Memory System

完成

```

docs/

```

含まれるもの

- README
- INDEX
- Bootstrap
- Architecture
- Pipeline
- UI
- Knowledge Sources
- ADR
- AI Startup Protocol

---

## Morning Ritual

安定化

```

run_morning_ritual.ps1

```

---

## GUI

LABOS UI

完成

```

Home
Overlay
Sentiment
Digest

```

---

# 作業ルール

AI作業は

```

1ターン = 1作業

```

必ず守る。

---

# AI作業開始ルール

AIは必ず

```

docs/ai_bootstrap_prompt.md

```

を前提にする。

---

# Knowledge System

GenesisPrediction v2 は

```

Chat Memory
↓
Repository Memory
↓
Runtime

```

構造で開発する。

---

END OF DOCUMENT
```
