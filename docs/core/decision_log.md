# Decision Log (GenesisPrediction v2)

Status: Active  
Purpose: Architecture decision record  
Last Updated: 2026-03-22

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

## Decision: Reference Memory is compacted for UI (short-form only)

対象

```text
scripts/scenario_engine.py
scripts/build_prediction_explanation.py
analysis/prediction/reference_memory_latest.json
analysis/explanation/prediction_explanation_latest.json
```

背景

Vector Memory により以下が取得可能になった。

* decision_log
* similar_cases
* historical_patterns
* historical_analogs

これにより Scenario / Prediction は recall を判断補助として利用できるようになった。

しかし、recall 結果をそのまま explanation artifact に渡すと、

* 長文になりすぎる
* document 全文や JSON 断片が混入する
* UI の可読性が崩れる
* memory 表示が explanation 本体より重くなる

問題が発生した。

問題

reference_memory は本来

```text
検索用データ
```

であり、

```text
そのまま表示用データではない
```

特に vector recall の戻り値には、

* decision_log の長い本文
* scenario / prediction snapshot の長文 summary
* explanation artifact の本文
* JSON に近い raw text

が含まれうる。

これをそのまま UI に出すと、

```text
UI = read-only
```

という原則は守れても、

```text
UI = readable
```

が崩れる。

結論

GenesisPrediction では

```text
Reference Memory = UI用に短文化して渡す
```

とする。

ルール

* decision_log → title のみ
* historical_pattern / historical_analog → title のみ
* scenario_snapshot / prediction_snapshot / signal_snapshot / explanation
  → title が汎用的すぎる場合は summary を短文化して使う
* JSON / 生テキスト / document 全文 → 除外
* 最大 6 件まで
* 短文化は analysis 側で行い、UI 側では行わない

責務分離

```text
vector DB        = 生データ（完全）
scenario_engine  = recall 実行
reference_memory_latest.json = recall materialize
build_prediction_explanation.py = 表示用 short-form 整形
UI               = 表示のみ
```

意図

* UI の可読性を守る
* explanation 本体の重心を守る
* memory の暴走を防ぐ
* 再現性を守る
* architecture の純度を保つ

補足

Vector Memory は

```text
reference-only memory
```

であり、意思決定の主体ではない。

また、

```text
UI は compacted reference_memory を読むだけ
```

であり、UI 側で要約・翻訳・整形をしてはならない。

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



## Decision: Full file delivery must use download format

背景

長時間スレ・重いコンテキスト環境において、

* 生成速度低下
* 出力途中欠落
* 行数不足の不完全生成
* コピペ時の人為ミス

が発生した。

特にスレ終盤では、

```text
苦し紛れの短文化生成
```

が確認された。

観察結果

* ダウンロード方式は生成が高速
* 重い環境でも安定
* 完全ファイルの欠落が発生しない
* コピペ事故が防げる

結論

GenesisPrediction では

```text
完全ファイルはダウンロード形式で提供する
```

とする。

ルール

* 長文コードはインライン出力禁止
* HTML / CSS / Python / PowerShell / JSON などはすべて対象
* スレ終盤では必須運用とする

意図

* 開発安定性の確保
* ミスの削減
* 再現性の維持

---

## Decision: Existing file must be verified before generation

背景

既存ファイルが存在するにも関わらず、

* 中身未確認のまま新規生成
* 構造不一致
* UI崩壊
* デバッグ困難

が発生した。

問題

AIが推測ベースでファイルを生成すると、

```text
実際の構造とズレる
```

リスクが高い。

結論

GenesisPrediction では

```text
既存ファイルを必ず確認してから生成する
```

とする。

ルール

* 生成前に必ず確認
* 既存ファイルがある場合はユーザーに提出させる
* 内容を確認せずに生成禁止
* 既存ファイルベースで修正する

意図

* 構造の整合性維持
* 上書き事故防止
* デバッグ性向上
* 再現性確保

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

```
