# GenesisPrediction Vector Memory Architecture
GenesisPrediction v2

Status: Active
Purpose: Qdrant を用いた Vector Memory 層の設計を固定し、過去判断・類似ケース・履歴要約を Scenario / Prediction の判断補助に使えるようにする
Last Updated: 2026-03-20
Location: docs/active/

---

# 0. Purpose

このドキュメントは

**GenesisPrediction v2 における Vector Memory Architecture を定義する**

ための設計文書である。

目的

- Qdrant 導入方針を固定する
- 何をベクターメモリ化するかを明確にする
- どの engine から参照するかを定義する
- analysis と vector memory の責務境界を固定する
- Scenario / Prediction 強化のための記憶レイヤを安全に追加する
- 将来の AI / 新しい会話 / 新しい PC でも同じ理解を再現できるようにする

GenesisPrediction において Vector Memory は

```text
Reference Memory Layer
````

である。

重要:

```text
Vector Memory は真実ではない
Vector Memory は参照記憶である
```

---

# 1. Core Principle

Vector Memory 設計の最重要原則はこれである。

```text
analysis = Single Source of Truth
Vector DB = reference-only memory
```

つまり

* 実行時の真実は analysis
* 記憶検索は vector memory
* 設計意図は docs
* 表示は UI

である。

Vector Memory は

```text
過去判断
類似ケース
歴史的類似
説明補助
```

を取り出すための層であり、

```text
analysis を上書きする層
```

ではない。

---

# 2. Position in Full Architecture

GenesisPrediction の責務分離は次のように維持する。

```text
scripts = 生成
data = 素材
analysis = 真実
app = 表示
docs = 設計
vector memory = 参照記憶
```

Vector Memory を加えた全体像は以下とする。

```text
Data Sources
↓
Pipeline (scripts)
↓
Analysis (SST)
↓
Prediction Layer
↓
UI
```

ただし Prediction Layer 内部では、次のように **Reference Memory Recall** を追加してよい。

```text
Observation
↓
Trend
↓
Signal
↓
Reference Memory Recall
↓
Scenario
↓
Prediction
↓
Explanation
↓
UI
```

ここでの Recall は

```text
Decision Recall
Historical Recall
Analog Recall
Explanation Recall
```

を意味する。

重要:

```text
Recall は判断材料
Prediction は最終要約
```

である。

---

# 3. Why Vector Memory Is Needed

Prediction Layer は latest だけでは弱い。

GenesisPrediction はすでに

```text
Memory is intelligence
```

という方向を持つ。

必要なのは

* 過去の似た判断を引くこと
* 過去の似た signal / scenario を引くこと
* 歴史的類似ケースを引くこと
* 説明表現の再利用を可能にすること
* 同じ議論や同じ設計判断を繰り返さないこと

である。

Vector Memory により GenesisPrediction は

```text
観測システム
↓
予測システム
↓
記憶付き判断支援システム
```

へ進化する。

---

# 4. Non-Negotiable Rules

Vector Memory 追加後も、以下は変更しない。

## Rule 1

```text
analysis remains SST
```

## Rule 2

```text
UI must not query vector memory directly
```

## Rule 3

```text
scripts / engines only may use vector recall
```

## Rule 4

```text
vector memory must never overwrite analysis
```

## Rule 5

```text
vector recall result should be materialized back into analysis
when needed for reproducibility
```

## Rule 6

```text
vector memory is support, not authority
```

---

# 5. What Vector Memory Is

Vector Memory は

**意味の近い過去情報を検索するための参照記憶層**

である。

使用技術の第一候補は

```text
Qdrant
```

とする。

役割

* embedding による類似検索
* tag / type / date による絞り込み
* 過去判断の再利用
* 類似状況の recall
* 歴史構造の recall
* explanation 表現の補助

重要:

```text
Qdrant = knowledge lookup
Qdrant ≠ source of truth
```

---

# 6. What Vector Memory Is Not

Vector Memory は以下ではない。

* analysis の代替
* docs の代替
* UI の直接データソース
* black-box prediction engine
* scenario probability を直接決める装置
* prediction を勝手に更新する装置
* truth store
* authoritative runtime artifact store

禁止事項

```text
vector memory が analysis を書き換える
vector memory が UI に直接値を返す
vector memory の recall を真実のように扱う
source artifact が無いのに recall 結果だけで判断を確定する
```

---

# 7. Qdrant Adoption Policy

GenesisPrediction では Qdrant を

```text
External Reference Memory Service
```

として導入する。

基本構造

```text
GenesisPrediction repo
  scripts/
  analysis/
  data/
  docs/

External Service
  qdrant
```

接続方針

* scripts / engines からのみ接続する
* UI から直接接続しない
* analysis artifact へ再物質化できるようにする
* failure-safe を必須とする
* Qdrant 停止時も main pipeline は継続できるようにする

重要:

```text
Qdrant unavailable != GenesisPrediction stop
```

---

# 8. Memory Types

Vector Memory で扱う対象は、まず以下の 4 系統とする。

---

## 8.1 Decision Log Memory

最優先。

対象

```text
docs/core/decision_log.md
将来の ADR
重要設計判断
```

目的

* 過去の architectural decision を再利用する
* AI が同じ議論を繰り返さないようにする
* 禁止された設計破壊を思い出せるようにする

例

* analysis を SST とする
* UI は read-only
* 完全ファイル運用
* UI は意味を計算しない

---

## 8.2 Prediction / Scenario History Memory

次に重要。

対象

```text
analysis/prediction/history/YYYY-MM-DD/prediction.json
analysis/prediction/history/YYYY-MM-DD/scenario.json
analysis/prediction/history/YYYY-MM-DD/signal.json
```

将来追加候補

```text
trend.json
historical_pattern.json
historical_analog.json
prediction_explanation.json
```

目的

* 類似 signal 構成の日を引く
* 類似 scenario balance の日を引く
* confidence drift の背景を見る
* watchpoints の再発を検出する

---

## 8.3 Historical Pattern / Analog Memory

Phase5 と直接接続する。

対象

```text
analysis/historical/*.json
analysis/prediction/historical_pattern_latest.json
analysis/prediction/historical_analog_latest.json
analysis/prediction/history/YYYY-MM-DD/historical_pattern.json
analysis/prediction/history/YYYY-MM-DD/historical_analog.json
```

目的

* 構造的に似た historical pattern を引く
* 類似 analog を引く
* Scenario の bias や watchpoints を補強する
* Prediction explanation を強化する

重要:

```text
Historical Pattern = abstract structure
Historical Analog = concrete case
```

---

## 8.4 Explanation Memory

将来効果が高い補助記憶。

対象

```text
analysis/explanation/prediction_explanation_latest.json
analysis/explanation/scenario_explanation_latest.json
analysis/explanation/signal_explanation_latest.json
analysis/explanation/fx_explanation_latest.json
analysis/explanation/world_explanation_latest.json
```

目的

* 似た判断の説明構造を引く
* must_not_mean の再利用
* 用語説明の整合
* 説明品質の安定化

重要:

```text
Explanation は新しい真実を作らない
```

この原則は Vector Memory 導入後も不変である。

---

# 9. Priority of Introduction

Vector Memory の導入順は次の通りとする。

## Phase 1

```text
Decision Log Memory
Prediction / Scenario History Memory
```

## Phase 2

```text
Historical Pattern / Analog Memory
```

## Phase 3

```text
Explanation Memory
```

理由

* まず decision recall による再発明防止を得る
* 次に prediction history recall による判断補助を得る
* その後 historical pattern を本格接続する
* explanation memory は土台が固まってから入れる

---

# 10. Data Boundary

analysis と vector memory の境界は明確に分離する。

## analysis の責務

* 最終成果物
* 再現可能な runtime artifact
* UI の正式 source
* history の保存
* 正式な prediction / scenario / signal / explanation artifact
* SST

## vector memory の責務

* 類似検索
* 過去判断検索
* 類似ケース検索
* 歴史的構造検索
* 説明補助検索
* recall 補助

重要整理

```text
analysis = truth
vector memory = recall
docs = design intent
UI = display
```

---

# 11. Allowed Callers

Vector Memory を呼んでよいのは

```text
scripts/*
prediction engines
supporting analysis builders
```

のみとする。

主な対象

* `scripts/scenario_engine.py`
* `scripts/prediction_engine.py`
* 将来の `scripts/signal_engine.py`
* 将来の explanation builders
* 将来の memory build / refresh scripts

禁止

* `app/static/*.html`
* `app/static/common/*.js`
* UI runtime fetch からの直接参照
* ブラウザ側での embedding / similarity 計算

---

# 12. Engine Integration Policy

## 12.1 Scenario Engine

Vector recall を最初に組み込む主対象は

```text
Scenario Engine
```

である。

理由

* Scenario は未来分岐生成層である
* Historical Pattern は Scenario を支援する層である
* 類似ケース recall と相性が良い
* watchpoints 拡張に使いやすい

Scenario で利用してよい recall

* 類似 signal 構成
* 類似 historical pattern
* 類似 analog
* 類似 decision history
* 類似 watchpoints

Scenario で使い得る出力

```text
similar_cases[]
recalled_patterns[]
recalled_analogs[]
decision_refs[]
recall_support_score
```

重要:

```text
Scenario Engine は recall を参考にしてよい
Scenario Engine は recall に支配されてはならない
```

---

## 12.2 Prediction Engine

次に入れる対象は

```text
Prediction Engine
```

である。

Prediction は公開用の最終要約であり、recall は補助情報として扱う。

Prediction で利用してよい recall

* dominant historical pattern
* dominant analog
* 類似過去判断
* 類似ケースの watchpoints
* 類似ケースの invalidation

Prediction で使い得る出力

```text
historical_context
analogous_cases
recall_note
recall_support_level
```

重要:

```text
Prediction は recall の要約を含んでよい
Prediction は recall だけで結論を決めてはならない
```

---

## 12.3 Signal Engine

Signal Engine への組み込みは将来候補とする。

用途

* 似た異常の再発検出
* persistence 類似検出
* regime shift 類似ケースの recall

ただし v1 では複雑化を避けるため後回しにする。

---

## 12.4 Explanation Builders

将来、explanation builders は Vector Memory を補助的に使ってよい。

用途

* 類似 explanation の構造参照
* must_not_mean の再利用
* ui_terms の整合
* 文体ではなく構造の安定化

禁止

```text
Vector Memory から explanation を丸ごとコピペして真実のように使うこと
```

---

# 13. Recall Query Design

Vector Recall は black-box にしない。

v1 では

```text
embedding similarity
+
tag filter
+
memory_type filter
+
date / time filter
```

の **hybrid recall** を基本とする。

例

* scenario engine が signal tags + trend direction で検索
* prediction engine が dominant scenario + drivers + watchpoints で検索
* decision recall が architecture tags + component name で検索

重要:

```text
Top-K は少数に保つ
v1 は 3〜5 件程度を基本とする
```

---

# 14. Chunking Policy

Qdrant へ投入する単位は **全文 1 件**ではなく、
**意味単位の chunk** を基本とする。

理由

* decision を粒度よく検索できる
* prediction history を日単位で扱える
* historical pattern を構造単位で扱える
* explanation を節単位で扱える

方針

## Decision Log

* 1 decision = 1 memory item

## Prediction History

* 1 date snapshot = 1 memory item
* 必要なら section chunk 化してもよい

## Historical Pattern

* 1 pattern = 1 memory item
* 1 analog = 1 memory item

## Explanation

* 1 artifact = 1 memory item
* または headline / summary / watchpoints 単位 chunk

---

# 15. Recommended Metadata Schema

各 memory item は最低限次を持つこと。

```json
{
  "memory_id": "string",
  "memory_type": "decision_log | prediction_snapshot | scenario_snapshot | signal_snapshot | historical_pattern | historical_analog | explanation",
  "as_of": "YYYY-MM-DD",
  "title": "string",
  "summary": "string",
  "tags": ["string"],
  "source_path": "string",
  "source_kind": "docs | analysis",
  "version": "string"
}
```

memory_type ごとの追加 field は許可する。

---

# 16. Example Payloads

## 16.1 Decision Log Memory

```json
{
  "memory_id": "decision-analysis-sst",
  "memory_type": "decision_log",
  "as_of": "2026-02",
  "title": "analysis を SST とする",
  "summary": "analysis is the only runtime truth; UI is read-only.",
  "tags": ["architecture", "SST", "analysis", "UI"],
  "source_path": "docs/core/decision_log.md",
  "source_kind": "docs",
  "version": "v1"
}
```

## 16.2 Prediction Snapshot Memory

```json
{
  "memory_id": "prediction-2026-03-19",
  "memory_type": "prediction_snapshot",
  "as_of": "2026-03-19",
  "title": "Prediction snapshot 2026-03-19",
  "summary": "overall_risk=guarded dominant_scenario=base_case confidence=0.42",
  "tags": ["prediction", "guarded", "base_case"],
  "source_path": "analysis/prediction/history/2026-03-19/prediction.json",
  "source_kind": "analysis",
  "version": "v1"
}
```

## 16.3 Historical Pattern Memory

```json
{
  "memory_id": "pattern-war-fiscal-currency-pressure",
  "memory_type": "historical_pattern",
  "as_of": "static",
  "title": "war → fiscal deterioration → currency pressure",
  "summary": "war-related structural stress pattern with fiscal and currency stress",
  "tags": ["historical", "war", "fiscal_stress", "currency_stress"],
  "source_path": "analysis/historical/war_patterns.json",
  "source_kind": "analysis",
  "version": "v1"
}
```

## 16.4 Explanation Memory

```json
{
  "memory_id": "prediction-explanation-latest",
  "memory_type": "explanation",
  "as_of": "2026-03-19",
  "title": "Prediction explanation latest",
  "summary": "headline + summary + why_it_matters + watchpoints",
  "tags": ["explanation", "prediction"],
  "source_path": "analysis/explanation/prediction_explanation_latest.json",
  "source_kind": "analysis",
  "version": "v1"
}
```

---

# 17. Materialization Back to Analysis

Vector recall を使った場合、必要に応じてその結果を analysis 側へ再物質化する。

目的

* 再現性の確保
* デバッグ容易性
* UI への将来表示余地
* recall 結果の監査可能性

推奨 artifact

```text
analysis/prediction/reference_memory_latest.json
```

将来分割してもよい。

```text
analysis/prediction/decision_recall_latest.json
analysis/prediction/historical_recall_latest.json
analysis/prediction/analog_recall_latest.json
```

---

# 18. Suggested Reference Memory Artifact Schema

v1 の最小例

```json
{
  "as_of": "YYYY-MM-DD",
  "engine_version": "v1",
  "query_context": {
    "source": "scenario_engine | prediction_engine",
    "tags": [],
    "notes": "string"
  },
  "decision_refs": [],
  "similar_cases": [],
  "historical_patterns": [],
  "historical_analogs": [],
  "recall_summary": "string",
  "status": "ok | unavailable"
}
```

重要:

```text
reference_memory_latest.json は recall の記録であり
prediction_latest.json の代替ではない
```

---

# 19. Failure Handling

Vector Memory は failure-safe でなければならない。

基本原則

```text
Qdrant failure must not stop Morning Ritual
```

失敗時の扱い

* Qdrant が停止している
* collection が存在しない
* recall が 0 件
* embedding 生成に失敗
* payload schema が不整合

この場合

* scenario / prediction は recall なしで継続する
* `status = unavailable` などを analysis artifact に残してよい
* pipeline は落とさない
* UI に直接影響させない

禁止

```text
recall unavailable を prediction unavailable に直結させること
```

---

# 20. Reproducibility Rule

Vector Memory は非決定性を増やしやすいため、再現性ルールを持つ。

v1 の原則

* recall query context を保存する
* top-k を固定する
* collection 名を固定する
* memory_type を固定する
* source_path を保持する
* recall summary を analysis 側に残す
* 重要判断に使った recall は history に保存できるようにする

重要:

```text
recall may assist
artifact must remain inspectable
```

---

# 21. Collection Design

Qdrant collection は最初は細かく分けすぎない。

推奨

## Option A

```text
genesis_reference_memory
```

単一 collection + memory_type filter

## Option B

```text
genesis_decision_memory
genesis_prediction_memory
genesis_historical_memory
genesis_explanation_memory
```

v1 推奨は Option A とする。

理由

* 管理が単純
* 再構築が容易
* filter で十分分離できる

---

# 22. Update Policy

Vector Memory の更新は、基本的に scripts 側の build / refresh により行う。

推奨 script

```text
scripts/build_vector_memory.py
scripts/vector_recall.py
```

将来候補

```text
scripts/refresh_vector_memory.ps1
scripts/build_reference_memory_artifact.py
```

更新タイミング候補

* manual rebuild
* Morning Ritual 後の refresh
* prediction history 保存後の index 追加
* decision_log 更新時の docs re-index

重要:

```text
Vector DB を手編集しない
source から再構築可能にする
```

---

# 23. Relation to Docs Architecture

docs は

```text
Repository Memory
```

であり、

```text
analysis = Single Source of Truth
docs = Single Source of Design Intent
```

である。

Vector Memory はこの両者を壊してはならない。

整理すると

```text
analysis = 実行時の真実
docs = 設計意図
vector memory = 検索しやすい参照記憶
```

つまり Vector Memory は

```text
truth でも constitution でもなく
searchable reference layer
```

である。

---

# 24. Relation to Historical Pattern Engine

Historical Pattern Engine は

```text
Scenario Engine を支援する入力層
```

である。

Vector Memory は Historical Pattern Engine と競合しない。

関係は次のように整理する。

```text
Historical Pattern Engine
= current signals と historical library の構造照合

Vector Memory
= past patterns / analogs / decisions / explanations の参照検索
```

両者は補完関係にある。

将来は以下を許可する。

* historical pattern output を vector index 化
* historical analog output を vector recall に組み込む
* scenario engine が両方を読む

重要:

```text
Pattern matching = structural logic
Vector recall = similarity lookup
```

---

# 25. Relation to Prediction Layer

Prediction Layer の正しい構造は

```text
Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction
↓
Explanation
```

である。

Vector Memory を入れても、この順序を壊してはならない。

許可される構造

```text
Observation
↓
Trend
↓
Signal
↓
Reference Memory Recall
↓
Scenario
↓
Prediction
↓
Explanation
```

禁止される構造

```text
Observation
↓
Vector Memory
↓
Prediction
```

```text
UI
↓
Vector Memory
↓
Prediction
```

```text
Vector Memory
↓
analysis overwrite
```

---

# 26. Security / Safety Policy

Vector Memory の利用においても、
GenesisPrediction の安全側原則を守る。

* source_path を保持する
* 出所不明の recall を使わない
* docs と analysis 由来のみを v1 の index 対象とする
* UI は vector DB に接続しない
* recall 結果の説明可能性を確保する

特に v1 では

```text
外部 web 情報を直接 Qdrant に混在させない
```

ことを推奨する。

まずは repo 内の docs / analysis のみを対象とする。

---

# 27. Future Expansion

将来追加候補

* multi-horizon recall
* drift-aware recall
* confidence-conditioned recall
* recall-to-explanation support
* decision assistant layer
* memory quality metrics
* recall evaluation benchmark
* analog explanation layer
* source citation support in recall artifacts

ただし v1 では複雑化しすぎない。

重要原則

```text
small, explainable, reproducible first
```

---

# 28. Initial Implementation Steps

## Step 1

Qdrant を external service として導入する。

## Step 2

`build_vector_memory.py` を作成する。

入力候補

```text
docs/core/decision_log.md
analysis/prediction/history/*
analysis/historical/*
analysis/explanation/*
```

## Step 3

`vector_recall.py` を作成する。

役割

* query 受付
* memory_type filter
* tag filter
* top-k search
* payload return

## Step 4

Scenario Engine に recall を追加する。

## Step 5

Prediction Engine に recall を追加する。

## Step 6

`analysis/prediction/reference_memory_latest.json` を生成する。

## Step 7

decision_log に導入判断を記録する。

---

# 29. Initial Scope Freeze

v1 の freeze 範囲は以下とする。

含める

* Qdrant 導入
* decision_log memory
* prediction / scenario history memory
* historical pattern / analog memory
* scenario engine integration
* prediction engine integration
* reference_memory_latest.json

含めない

* UI direct integration
* automated action
* black-box ML retrieval scoring
* free-form explanation generation from vector DB
* external internet corpus indexing
* trading automation

---

# 30. Final Design Principle

GenesisPrediction Vector Memory の設計原則を一言で言うと

```text
Searchable memory without breaking SST
```

日本語では

```text
SST を壊さない検索可能記憶
```

である。

---

# 31. Final Summary

GenesisPrediction の Vector Memory は

```text
Qdrant-based Reference Memory Layer
```

として設計する。

役割

```text
Decision Recall
Historical Recall
Analog Recall
Explanation Recall
```

境界

```text
analysis = truth
docs = design intent
vector memory = recall
UI = display
```

重要なのは

```text
Vector Memory を真実にしない
```

ことである。

Vector Memory は GenesisPrediction を

```text
観測
↓
予測
↓
記憶付き判断支援
```

へ進化させるための補助層である。

---

END OF DOCUMENT

````
