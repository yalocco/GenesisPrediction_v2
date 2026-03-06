# ADR 0001: Repository Memory を採用する

Status: Accepted  
Date: 2026-03-06

---

## Context

GenesisPrediction v2 の開発は長期間にわたり、  
AIと人間の共同開発として進んでいる。

従来の進め方では、

- Chatスレッドの記憶に依存する
- スレが変わると設計説明をやり直す必要がある
- UI変更やPipeline変更の意図が失われる
- 作業手順や依存関係の再説明が必要になる

という問題があった。

この状態では、長期運用・継続開発・AI交代に弱い。

---

## Decision

GenesisPrediction v2 は  
**Repository Memory** を採用する。

Repository Memory とは

docs/

に保存される設計知識である。

この層には以下を含む。

- repo_map.md
- repo_architecture.md
- project_status.md
- pipeline_system.md
- ui_system.md
- genesis_brain.md
- chat_operating_rules.md
- ai_bootstrap_prompt.md

Repository Memory は  
Chat Memory に依存しない **永続的な設計知識層** として扱う。

---

## Consequences

### Positive

- スレが変わっても開発継続可能
- AIが構造を理解した状態で作業開始できる
- 手順や設計意図の再説明が減る
- 人間とAIの認識ズレを減らせる
- 長期運用に強くなる

### Negative

- docs の更新コストが増える
- 設計変更時にコードだけでなく docs も更新する必要がある
- 古い docs を放置すると逆に混乱の原因になる