# Decision Log (GenesisPrediction v2)

Status: Active  
Purpose: Architecture decision record  
Last Updated: 2026-03-21

---

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

**重要な設計判断**

を記録する。

目的

- 将来の自分が理由を思い出せるようにする
- AIが設計意図を理解できるようにする
- 同じ議論を繰り返さない

---

# 2026-03

## Decision: Introduce Vector Memory Architecture (Qdrant)

対象

```text
docs/active/vector_memory_architecture.md
Qdrant
scripts/build_vector_memory.py
scripts/vector_recall.py
scripts/scenario_engine.py
scripts/prediction_engine.py
````

背景

GenesisPrediction は

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
```

の構造を持つ。

ただし latest だけでは

* 過去の似た判断
* 類似 scenario
* 類似 signal
* historical analog
* decision history

を十分に活かせない。

また、

```text
decision_log
historical pattern
prediction history
explanation artifacts
```

を

**検索可能な参照記憶**

として使いたい要求が生まれた。

問題

既存構造を壊したまま memory を追加すると、

* analysis 以外に「真実」が増える
* UI が記憶検索を始める
* prediction が black-box 化する
* docs / analysis / memory の責務が混ざる
* 再現性が下がる

危険がある。

結論

GenesisPrediction では

```text
Vector Memory = reference-only memory
```

とする。

固定ルール

```text
analysis = Single Source of Truth
Vector DB = reference memory only
UI must not query vector memory directly
scripts / engines only may use vector recall
vector memory must never overwrite analysis
```

採用方針

* Qdrant を external reference memory service として使う
* まずは docs / analysis 由来の memory のみを index する
* Scenario / Prediction が recall を補助入力として使う
* recall 結果は必要に応じて analysis 側へ materialize する
* Qdrant 停止時でも pipeline は継続する

優先 memory 対象

```text
1. decision_log memory
2. prediction / scenario history memory
3. historical pattern / analog memory
4. explanation memory
```

主な接続先

```text
scenario_engine.py
prediction_engine.py
```

重要原則

```text
Vector Memory は判断補助
Prediction / Scenario の代替ではない
```

---

## Decision: Open WebUI Integration with Qdrant

背景

Open WebUI を Qdrant に接続し、

Knowledge / File を vector search 可能にした。

確認結果

* Qdrant 接続成功
* collection 作成確認
* point 保存確認

```text
open-webui_files
open-webui_knowledge
```

結論

Open WebUI → Qdrant 接続は成立。

---

## Decision: Qdrant instance can be shared

* Open WebUI と GenesisPrediction は同一 Qdrant を共有してよい

ただし：

```text
collection は必ず分離する
```

---

## Decision: Collection must be separated

Open WebUI と GenesisPrediction の collection を分離する。

```text
Open WebUI:
  open-webui_files
  open-webui_knowledge

GenesisPrediction:
  genesis_reference_memory
```

理由

* 管理責任の分離
* 検索ノイズ防止
* 将来の再構築容易性

---

## Decision: Conversation is NOT auto-vectorized

* Open WebUI の会話ログは自動で Qdrant に保存されない
* 会話はそのままでは記憶対象としない

---

## Decision: Memory is promoted, not raw

* 会話全文を保存しない
* 確定した判断のみ記憶に昇格する

対象

```text
decision
rule
insight
```

非対象

```text
仮説
試行錯誤
雑談
```

---

## Decision: Decision Log is primary memory source

* Vector Memory の第一優先は decision_log
* build_vector_memory.py は decision_log を最優先で取り込む

---

## Decision: build_vector_memory.py is single entrypoint

* vector memory 構築は build_vector_memory.py に統一
* スクリプトを増やさない

---

## Decision: WorldDate = LOCAL DATE

対象

```text
scripts/run_morning_ritual.ps1
```

旧仕様

```text
WorldDate = UTC yesterday
```

問題

```text
missing raw news
```

原因

ニュース raw データは

```text
data/world_politics/YYYY-MM-DD.json
```

として

**ローカル日付で保存されている。**

そのため

```text
UTC yesterday
```

と

```text
LOCAL DATE
```

がズレるケースが発生した。

結論

```text
WorldDate = LOCAL DATE
```

---

# 2026-02

## Decision: analysis を SST とする

GenesisPrediction v2 の真実は

```text
analysis/
```

のみ。

理由

```text
scripts = 生成
data = 素材
analysis = 最終成果
UI = 表示
```

責務分離を明確化するため。

---

## Decision: UI は read-only

対象

```text
app/static/*.html
```

ルール

```text
UIはanalysisを読むだけ
```

理由

* 再現性
* デバッグ容易性
* 責務分離

---

## Decision: 完全ファイル運用

ルール

```text
差分提案禁止
完全ファイルのみ
```

理由

* コピペ事故防止
* AI生成の途中欠落防止

---

# Future Decisions

将来ここに追加予定

```text
Prediction engine architecture
Trend3 logic
Scenario engine
Risk scoring
FX decision model
Vector memory implementation freeze
Reference memory artifact schema freeze
Qdrant operational rule
```

---

END OF DOCUMENT

````
