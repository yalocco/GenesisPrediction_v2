# ADR (Architecture Decision Records)

このディレクトリは  
GenesisPrediction v2 の **重要な設計判断** を記録するための場所です。

ADR = Architecture Decision Record

目的：

- 「なぜこの設計にしたのか」を残す
- 将来、AIや人間が設計意図を復元できるようにする
- スレ変更 / PC変更 / AI変更があっても、判断理由を失わないようにする

---

# ADR の基本ルール

1. 重要な設計判断だけを書く  
2. 1つのADR = 1つの判断  
3. 「何を決めたか」より **なぜそう決めたか** を重視する  
4. 一度作ったADRは削除しない  
5. 設計変更があった場合は、新しいADRを追加する  

---

# 記述する内容

各ADRには以下を含める。

- Title
- Status
- Date
- Context
- Decision
- Consequences

---

# ステータス

- Proposed
- Accepted
- Superseded
- Deprecated

通常は `Accepted` を使う。

---

# 命名規則

0001-short-title.md  
0002-short-title.md  
0003-short-title.md  

例：

0001-repository-memory.md  
0002-analysis-as-sst.md  

---

# 現在のADR

- 0001 Repository Memory を採用する
- 0002 analysis/ を Runtime SST とする

---

# このADRの役割

GenesisPrediction v2 は  
**AIと人間の共同開発プロジェクト**である。

そのため、単なるコードやREADMEだけではなく、  
**設計判断の履歴** を残す必要がある。

ADRは

「なぜこの設計にしたか」

を残すための公式記録である。