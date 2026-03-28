# General Decision Log (Genesis Assistant)

Status: Active  
Purpose: General decision memory for the companion AI  
Last Updated: 2026-03-28

---

## Purpose

Record important decisions that affect future behavior, ensuring consistency, traceability, and improved decision quality over time.

This log is for the **general assistant only**.

It stores:

- long-term behavioral decisions
- workflow decisions for the companion AI
- reasoning and operation rules that should remain reusable

It does **not** store GenesisPrediction-specific architecture rules.

---

## Core Principle

Not all decisions should be stored.

Only store decisions that:

- have long-term impact
- affect future behavior
- improve consistency

---

## Entry Format

Each entry should follow this structure:

---

### [DATE] Decision Title

#### Context

- What situation led to this decision?

#### Decision

- What was decided?

#### Reason

- Why was this chosen?

#### Alternatives Considered

- What other options existed?

#### Impact

- How does this affect future behavior?

---

## Example

### [2026-03-28] Separate Strict AI and General AI

#### Context

Need to handle both precise engineering tasks and flexible thinking.

#### Decision

Create two modes:

- strict mode (GenesisPrediction)
- general mode (companion AI)

#### Reason

Mixing both behaviors caused inconsistency and instability.

#### Alternatives Considered

- single unified mode
- dynamic behavior switching without clear separation

#### Impact

- improved consistency
- clearer role separation
- better output quality

---

## What to Record

### 1. Architecture Decisions

- system design choices
- separation of layers
- tool integration strategy

---

### 2. Workflow Decisions

- how tasks are executed
- preferred methods
- execution patterns

---

### 3. Tool Selection

- model usage roles
- framework choices
- infrastructure decisions

---

### 4. Behavior Rules

- response style changes
- rule adjustments
- constraints added

---

## What NOT to Record

### 1. Temporary Decisions

- quick fixes
- temporary workarounds

---

### 2. Experimental Ideas

- untested approaches
- incomplete thoughts

---

### 3. Minor Choices

- trivial preferences
- low-impact decisions

---

### 4. GenesisPrediction-Specific Rules

Do not store rules that belong to the GenesisPrediction system, such as:

- analysis = SSOT
- UI is display-only
- UI must not translate
- GenesisPrediction pipeline constraints
- GenesisPrediction-specific architecture rules

Those must remain in the dedicated GenesisPrediction decision log.

---

## Update Rules

- Append only (do not overwrite past entries)
- Keep entries concise
- Avoid duplication

---

## Retrieval Rules

When answering:

1. Check if a similar decision exists
2. If yes → reuse reasoning
3. If no → proceed normally

Priority:

1. general decision log
2. attached general knowledge
3. general reasoning
4. web search only when current external information is required

---

## Consistency Rule

- Do not contradict past decisions unless explicitly updated
- If overridden:
  - create a new entry
  - explain why

---

## Qdrant Preparation Rule

Decision logs are ideal for vector search.

Keep entries:

- structured
- concise
- meaningful

Avoid:

- long narratives
- noise
- duplication

---

## Summary

The decision log is:

- the memory of past choices
- the foundation of consistency
- the key to stable AI behavior

---

### [2026-03-28] Separate GenesisPrediction and General AI Decision Logs

#### Context

GenesisPrediction と汎用AIの両方で decision_log を運用していたが、
両者の性質（機械的判断 vs 思考支援）が異なるため、
同一ログで管理すると混在のリスクがあった。

#### Decision

decision_log を以下の2つに分離する。

- decision_log.md（GenesisPrediction用）
- 05_general_decision_log.md（汎用AI用）

#### Reason

GenesisPrediction は分析・予測システムであり、
厳密性・再現性が最優先される。

一方、汎用AIは思考支援・意思決定支援を目的とし、
柔軟性と文脈理解が重要となる。

両者を同一ログで管理すると、

- 思考ログが分析ロジックに混入する
- 機械的ルールが思考に干渉する
- RAG 検索で誤ヒットが起こる

といった問題が発生するため分離が必要。

#### Alternatives Considered

- 単一の decision_log で管理する
- タグやセクションで分ける

しかし、完全分離の方が安全性と明確性が高いと判断した。

#### Impact

- GenesisPrediction の安定性が向上
- 汎用AIの思考の自由度が維持される
- 将来的な拡張（自動化・RAG連携）が容易になる

---

### [2026-03-28] Adopt Semi-Automatic Decision Log Operation

#### Context

decision_log を運用するにあたり、
完全手動では負担が大きく、完全自動ではノイズが増える懸念があった。

そのため、効率と精度のバランスを取る運用方式が必要だった。

#### Decision

decision_log を「半自動（AI提案＋ユーザー承認）」で運用する。

- AIが重要な判断を検知
- AIが保存を提案
- ユーザーが承認
- 承認後にdecision_logとして記録

#### Reason

完全手動では記録漏れが発生しやすく、
完全自動では不要なログが蓄積される。

半自動にすることで、

- 重要な判断の取りこぼしを防ぐ
- ノイズの混入を防ぐ
- ユーザーの意思決定を尊重する

というバランスが取れる。

#### Alternatives Considered

- 完全手動運用
- 完全自動運用

しかし、

- 手動 → 負担増・漏れ発生
- 自動 → ノイズ増加・品質低下

のため採用しなかった。

#### Impact

- decision_log の品質が安定する
- AI の判断が継続的に改善される
- 長期的な一貫性が向上する
- 将来的な自動化への移行が容易になる

---

END OF DOCUMENT
