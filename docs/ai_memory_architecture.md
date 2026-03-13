# AI Memory Architecture
(GenesisMemory)

## 1. Purpose

GenesisMemory は AI に長期記憶能力を与えるための外部システムである。

本システムの目的は以下である。

- AI の長期記憶を実現する
- 会話の継続性を保持する
- 過去の意思決定や作業履歴を保持する
- プロジェクト固有の運用ルールを保持する
- RAG とは異なる Memory System を構築する

GenesisMemory は **GenesisPrediction 本体を変更せずに拡張できる外部システム**として設計する。

---

# 2. Design Principles

GenesisMemory は以下の原則に基づいて設計する。

### 2.1 Prediction System を壊さない

GenesisPrediction 本体には Memory 機能を組み込まない。

Memory System は外部サービスとして提供する。

```

GenesisPrediction
|
v
GenesisMemory API
|
v
Memory Storage

```

この設計により

- システム独立性
- 拡張性
- 再利用性

を確保する。

---

### 2.2 RAG と Memory を分離する

RAG は **知識検索**であり、Memory は **経験の蓄積**である。

| System | Purpose |
|------|------|
| RAG | 知識検索 |
| Memory | 経験・履歴・ルール |

GenesisMemory は RAG の代替ではない。

---

### 2.3 記憶は3種類に分類する

GenesisMemory では記憶を以下の3種類に分類する。

```

Semantic Memory
Episodic Memory
Procedural Memory

```

この分類は人間の記憶モデルに基づく。

---

# 3. Memory Types

---

# 3.1 Semantic Memory

## 概要

Semantic Memory は **意味知識**を保存する。

これは「事実」「概念」「関係」を表す記憶である。

---

## 保存対象

例

- プロジェクト構造
- 設計書
- 用語
- ドメイン知識
- 技術仕様
- ユーザーの安定した嗜好

---

## 例

```

GenesisPrediction architecture
Scenario Engine design
Prediction Layer structure

```

---

## Storage

Semantic Memory は **Vector Database** に保存する。

候補

- Qdrant
- Chroma
- Weaviate
- Milvus

GenesisMemory では **Qdrant を推奨する**。

---

## 主な用途

- 意味検索
- 関連概念検索
- 設計参照
- 類似情報探索

---

# 3.2 Episodic Memory

## 概要

Episodic Memory は **出来事の記憶**である。

これは「いつ」「何が起きたか」を保存する。

---

## 保存対象

例

- 会話履歴
- 作業ログ
- 意思決定
- スレッド履歴
- エラー対応
- 実験結果

---

## 例

```

2026-03-13
GenesisMemory architecture discussion started

```

---

## Storage

Episodic Memory は **時系列データベースまたは RDB** に保存する。

候補

- PostgreSQL
- SQLite
- JSON Event Store

初期実装では **SQLite または PostgreSQL** を使用する。

---

## 主な用途

- 会話の継続
- 決定履歴
- タスク進行状況
- 過去作業の追跡

---

# 3.3 Procedural Memory

## 概要

Procedural Memory は **行動ルールや手順**を保存する。

AI がどのように振る舞うべきかを定義する。

---

## 保存対象

例

- 作業ルール
- runbook
- 禁止事項
- coding rules
- output policy
- 作業手順
- thread templates

---

## 例

```

差分提案は禁止
完全ファイルのみ提示

```

---

## Storage

Procedural Memory は **Rule Database** に保存する。

候補

- PostgreSQL
- JSON
- YAML

---

## 主な用途

- AIの行動制御
- 出力フォーマット統一
- 作業ルール適用
- 運用ポリシー保持

---

# 4. System Architecture

GenesisMemory の基本構造は以下である。

```

User
|
v
Chat Interface (Open-WebUI)
|
v
Conversation Orchestrator
|
+-----------------------------+
|             |               |
v             v               v
Semantic     Episodic       Procedural
Memory       Memory         Memory
|             |               |
+-------------+---------------+
|
v
Memory Retrieval Layer
|
v
Context Builder
|
v
LLM
|
v
Response + Writeback

```

---

# 5. Storage Layer

GenesisMemory の Storage は以下で構成される。

```

Vector DB
Event DB
Rule DB

```

---

## 5.1 Vector Database

用途

- Semantic Memory

候補

- Qdrant
- Chroma
- Weaviate

推奨

**Qdrant**

理由

- Docker 対応
- 高速
- metadata 検索対応

---

## 5.2 Event Database

用途

- Episodic Memory
- session logs
- decision logs

候補

- PostgreSQL
- SQLite

---

## 5.3 Rule Database

用途

- Procedural Memory
- AI 行動ルール

候補

- PostgreSQL
- JSON / YAML

---

# 6. Retrieval Architecture

Memory System は **保存より検索が重要**である。

GenesisMemory は以下の順序で Memory を取得する。

---

## Retrieval Priority

```

1 Procedural Memory
2 Current User Intent
3 Recent Episodic Memory
4 Relevant Semantic Memory
5 Archive Memory

```

---

## Context Builder

LLM に渡す Context は以下を合成して生成する。

```

Task Context
Relevant Knowledge
Recent Events
Applicable Rules

```

---

# 7. Memory Lifecycle

すべての情報を永久保存しない。

Memory には寿命を持たせる。

---

## Lifecycle

```

capture
↓
classify
↓
store
↓
retrieve
↓
update
↓
archive

```

---

## 重要概念

Memory Item は以下の属性を持つ。

```

confidence
importance
created_at
last_used
status

```

---

# 8. Integration with GenesisPrediction

GenesisMemory は **GenesisPrediction の外部サービス**として接続する。

```

GenesisPrediction
|
+---- Memory Query API
|
+---- Memory Write API

```

この設計により

- Prediction System を壊さない
- Memory を独立進化できる
- 他プロジェクトでも再利用可能

---

# 9. Docker Architecture

推奨 Docker 構成

```

genesis-memory

memory-api
memory-worker
qdrant
postgres
redis
open-webui-adapter

```

---

## memory-api

機能

- memory query
- memory write
- context builder

---

## memory-worker

機能

- embedding
- classification
- summarization

---

## qdrant

用途

Vector Database

---

## postgres

用途

Episodic / Procedural storage

---

## redis

用途

queue / cache

---

## open-webui-adapter

用途

Open-WebUI 連携

---

# 10. Minimum Viable System

最初の実装では以下を作る。

```

Semantic Memory
Episodic Memory
Procedural Memory
Context Builder
Memory API
Open-WebUI Adapter

```

---

# 11. Future Extensions

将来的には以下を追加可能。

- knowledge graph
- long-term agent memory
- multi-agent shared memory
- autonomous summarization
- memory confidence scoring
- memory decay system

---

# 12. Summary

GenesisMemory は AI の長期記憶システムである。

Memory は以下の3種類に分類する。

```

Semantic Memory
Episodic Memory
Procedural Memory

```

GenesisMemory は GenesisPrediction 本体とは独立した外部システムとして構築する。

これにより

- AIの記憶力
- 会話継続性
- 作業ルール保持
- プロジェクト知識保持

を実現する。
```
