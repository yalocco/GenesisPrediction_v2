# Genesis Brain (GenesisPrediction v2)

Version: 4.0
Status: Active (RAG Stable)
Last Updated: 2026-03-20

---

# 0. Vision（Genesisの意味）

GenesisPrediction は単なるソフトウェアではない。

これは

**個人AI研究所（Personal AI Research Lab）**

である。

Genesis の意味：

1. すべてを失った後の「再出発」
2. 創世記（Genesis）からの思想

世界の混沌から

**秩序・意味・危険信号**

を抽出するためのシステム。

---

# 1. Core Purpose（核心目的）

目的は未来を当てることではない。

目的は

**危険を早く知ること**

である。

理由：

- 家族を守る
- 資産を守る
- 次世代へつなぐ

これは

**Global Risk Observation System**

である。

---

# 2. Personal AI Research Lab

構造：

```

Human（設計）
+
AI（実装）
+
Observation System（観測）

```

開発：

```

Human → 設計
AI → 実装
Human → 評価

```

AIはツールではなく

**研究パートナー**

---

# 3. Continuous Observation（観測思想）

未来予測の本質は

**継続的観測**

GenesisPrediction は

**Daily Observation System**

---

# 4. Morning Ritual（最重要）

Daily Pipeline：

```

Fetch
↓
Analyze
↓
Sentiment
↓
Digest
↓
Overlay

```

これは

**システムの心拍（Heartbeat）**

であり、

最優先は

**毎日止まらないこと**

---

# 5. 最重要構造（絶対ルール）

## 🔥 Core Architecture

```

scripts → analysis → UI

```

---

## scripts（生成層）

- データ生成（工場）
- 真実は持たない
- 再生成可能

---

## analysis（SST）

**Single Source of Truth**

- 生成済みJSON成果物
- 唯一の真実
- UI・判断の唯一の根拠

### ⚠️ 最重要定義

```

analysis = generated artifacts (JSON)
analysis is NOT API
analysis is NOT FastAPI
analysis is NOT runtime logic

```

---

## UI（表示層）

- 読み取り専用
- 計算禁止
- analysis を表示するだけ

```

UI does NOT calculate
UI only reads analysis

```

---

# 6. 責務分離（Separation of Concerns）

```

scripts
生成（計算・加工）

analysis
真実（成果物）

UI
表示のみ

```

---

# 7. データフロー（固定）

```

scripts → analysis → UI

```

---

# 8. Prediction構造（絶対順序）

Predictionは単独で存在しない。

```

Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction

```

### ルール

- Scenario を飛ばしてはいけない
- Prediction は最終要約
- 上位レイヤが本体

---

# 9. 実行モデル

GenesisPrediction は

**イベント駆動ではない**

## 実行方式

```

Morning Ritual（バッチ実行）

```

## 実際の流れ

```

scripts 実行（毎日）
↓
analysis 生成
↓
UI が latest を読む

```

---

## ❌ 誤った理解（禁止）

```

UI → API → LLM

```

これはチャットアプリ構造であり、

GenesisPredictionではない

---

# 10. 安定性優先

- 完走最優先
- 再現性優先
- 不安定状態で公開しない

---

# 11. UI思想

- 派手さより安定
- 統一された設計
- 壊れないUI

---

# 12. 開発ルール

- 1ターン = 1タスク
- 完全ファイルのみ
- 差分禁止
- UIは表示のみ
- 計算は scripts / analysis 側のみ

---

# 13. 進化の方向

```

News
↓
Sentiment
↓
Trend Detection
↓
Signal
↓
Scenario
↓
Prediction

```

---

# 14. LABOS

公開研究所として展開予定

提供候補：

- Risk Digest
- FX Monitoring
- Scenario Analysis

---

# 15. Legacy

目的は

**知識・データ・システムを残すこと**

---

# 16. 研究サイクル

```

Observation
↓
Hypothesis
↓
Verification
↓
Freeze

```

---

# 17. RAG強化ルール（AI用）

## Absolute Rules

- analysis is Single Source of Truth
- analysis = generated JSON artifacts only
- analysis is NOT API / NOT FastAPI

- scripts generate artifacts only
- UI is read-only (no calculation)

- architecture:
  scripts → analysis → UI

- prediction flow:
  Observation → Trend → Signal → Scenario → Prediction

- FastAPI / LLM call flow is NOT core architecture

---

# END
```
