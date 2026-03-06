# ADR 0002: analysis/ を Runtime SST とする

Status: Accepted  
Date: 2026-03-06

---

## Context

GenesisPrediction v2 では

- scripts がデータを生成する
- UI が結果を表示する
- data/ には素材が入る

という構造を持つ。

しかし過去には

- UIで不足分を補おうとする
- どのJSONが真実か曖昧になる
- data/ と analysis/ の役割が混ざる
- GUI側で再計算したくなる

といった混乱が起こり得た。

この状態では再現性が下がり、  
どこを修正すべきか判断しづらくなる。

---

## Decision

GenesisPrediction v2 では

analysis/

を **Runtime SST (Single Source of Truth)** とする。

ルール

scripts → analysis を生成  
analysis → 唯一の真実  
UI → analysis を読むだけ  
data/ → 素材  

UIはanalysisだけを読み、  
UI側で再計算・再生成・補正ロジックを持たない。

---

## Consequences

### Positive

- どこが真実か明確になる
- UIの責務が軽くなる
- scripts / analysis / UI の責務分離が明確になる
- 障害切り分けが速くなる
- 再現性が高くなる

### Negative

- analysis設計が弱いと全体に影響する
- UIでの応急処置がしづらくなる
- scripts側の整備責任が大きくなる