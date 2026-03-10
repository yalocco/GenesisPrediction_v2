# Prediction Runtime

Status: Active  
Purpose: Signal → Scenario → Prediction を日次運用の中で安定実行する Runtime 仕様を固定する  
Last Updated: 2026-03-09

---

# 0. Purpose

このドキュメントは GenesisPrediction v2 における **Prediction Runtime** を定義する。

Prediction Runtime の目的は次の通りである。

- Signal Layer / Scenario Layer / Prediction Layer の実行順を固定する
- Morning Ritual への統合点を明確にする
- Output Artifact の保存先と責務を固定する
- Early Warning Engine の位置づけを明確にする
- UI が参照すべき Runtime SST を安定化する

重要原則

```text
Prediction Runtime は prediction logic を実行する運用層である
```

これは設計思想そのものではなく、
**毎日の心拍の中で Prediction Layer をどう動かすか**
を定める文書である。

---

# 1. Runtime Position in GenesisPrediction

GenesisPrediction の全体流れは次のとおりである。

```text
Data Sources
↓
Pipeline (scripts)
↓
Analysis (SST)
↓
Prediction Layer Runtime
↓
UI
↓
LABOS
```

Prediction Runtime は

```text
analysis build の後
UI update の前
```

に配置される。

つまり Prediction Runtime は

- Observation の上に乗る
- Trend の結果を受け取る
- Signal / Scenario / Prediction を生成する
- その成果物を UI と History に渡す

という役割を持つ。

重要原則

```text
Prediction Runtime は analysis を完成させる最後段の一部である
```

---

# 2. Runtime Scope

Prediction Runtime が担当する範囲は以下である。

## 2.1 In Scope

- trend_latest.json を入力として読む
- signal_latest.json を生成する
- scenario_latest.json を生成する
- prediction_latest.json を生成する
- Early Warning を生成する
- prediction history 用の凍結データを生成する
- UI 用 latest artifact を更新する

## 2.2 Out of Scope

Prediction Runtime は以下を担当しない。

- ニュース収集
- sentiment 再計算
- digest 再構築
- overlay 再生成
- UI 側ロジック実行
- 手動判断の代行

重要原則

```text
Prediction Runtime は観測を作らず、観測から予測構造を作る
```

---

# 3. Core Runtime Flow

Prediction Runtime の基本実行順は以下で固定する。

```text
analysis build
↓
trend build
↓
signal build
↓
scenario build
↓
prediction build
↓
early warning build
↓
prediction history freeze
↓
UI update
```

GenesisPrediction における最重要流れは次である。

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

Prediction Runtime はこの流れを **毎日再現可能な形で運用する心拍** である。

重要原則

```text
Observation から直接 Prediction を作らない
```

---

# 4. Inputs

Prediction Runtime の主要入力は analysis/ にある Runtime SST である。

最低限必要な入力は次の通り。

```text
analysis/trend/trend_latest.json
analysis/daily_summary_latest.json
analysis/sentiment_latest.json
analysis/health_latest.json
```

将来的には以下も補助入力として利用可能。

```text
analysis/observation/*.json
analysis/anchors/*.json
analysis/digest/view_model_latest.json
analysis/fx/*.json
analysis/prediction_history/
```

ただし Runtime の直接入力として最重要なのは

```text
trend_latest.json
```

である。

理由

- Trend は Observation の変化方向をすでに整理している
- Signal は Trend から兆候を抽出する層である
- Runtime の責務分離が明確になる

重要原則

```text
Signal Runtime の主入力は Trend である
```

---

# 5. Signal Runtime

Signal Runtime は Trend を読んで、
**注意すべき兆候** を構造化する。

## 5.1 Role

Signal の役割は次の通り。

- persistence を検出する
- anomaly を検出する
- reversal を検出する
- acceleration を検出する
- regime_shift を検出する

Signal は「未来そのもの」ではない。
Signal は

```text
未来分岐を作るための警告材料
```

である。

## 5.2 Output

最低出力

```text
analysis/prediction/signal_latest.json
```

想定項目例

```text
as_of
signals[]
overall_signal_strength
signal_confidence
source_trends
notes
```

## 5.3 Runtime Rule

- Trend の説明を再掲するだけで終わらない
- ノイズを Signal と誤認しない
- 単発異常より持続兆候を優先する
- 後段の Scenario が使える形で構造化する

重要原則

```text
Signal は Early Warning の材料である
```

---

# 6. Scenario Runtime

Scenario Runtime は Signal を読んで、
**未来分岐** を構造化する。

## 6.1 Role

Scenario の役割は次の通り。

- best_case を定義する
- base_case を定義する
- worst_case を定義する
- drivers を整理する
- watchpoints を整理する
- invalidation_conditions を整理する

Scenario は単なる作文ではない。
Signal と Trend をもとにした

```text
説明可能な未来分岐
```

である。

## 6.2 Output

最低出力

```text
analysis/prediction/scenario_latest.json
```

想定項目例

```text
as_of
horizon_days
best_case
base_case
worst_case
probabilities
drivers
watchpoints
invalidation_conditions
scenario_confidence
```

## 6.3 Runtime Rule

- Scenario を 1 本だけにしない
- 未来分岐は最低 3 系統を維持する
- すべての Scenario に理由を持たせる
- watchpoints を必須にする
- invalidation_conditions を持たせる

重要原則

```text
Scenario を持たない Prediction は禁止
```

---

# 7. Prediction Runtime

Prediction Runtime は Scenario を読み、
**公開用の最終要約** を生成する。

## 7.1 Role

Prediction の役割は次の通り。

- dominant_scenario を定義する
- overall_risk を定義する
- confidence を定義する
- summary を生成する
- drivers / watchpoints を公開用に整理する
- Early Warning 用の最終判定を補助する

Prediction は主役ではない。
Prediction は

```text
Scenario の公開用サマリー
```

である。

## 7.2 Output

最低出力

```text
analysis/prediction/prediction_latest.json
```

想定項目例

```text
as_of
dominant_scenario
overall_risk
confidence
summary
drivers
watchpoints
invalidation_conditions
early_warning_status
horizon_days
```

## 7.3 Confidence Rule

confidence は

```text
当たる確率
```

ではない。

confidence は

```text
現在の観測とシナリオ整合性の強さ
```

である。

評価に使う要素例

- データ十分性
- trend の明瞭さ
- signal の強さ
- scenario の整合性
- watchpoints の具体性

重要原則

```text
confidence を飾りにしない
```

---

# 8. Early Warning Engine

Early Warning Engine は Prediction Runtime の中核である。

GenesisPrediction において重要なのは

```text
正解を当てることではなく
危険を早く知ること
```

である。

そのため Early Warning Engine は
Prediction Runtime の一部として明示的に設計する。

## 8.1 Purpose

- 危険分岐の早期検出
- watchpoints の運用化
- warning 状態の安定表示
- daily hypothesis の優先監視ポイント抽出

## 8.2 Inputs

Early Warning Engine は以下を使う。

```text
signal_latest.json
scenario_latest.json
prediction_latest.json
health_latest.json
```

## 8.3 Output

最低出力

```text
analysis/prediction/early_warning_latest.json
```

想定項目例

```text
as_of
status
level
headline
summary
triggered_signals
key_watchpoints
escalation_reasons
recommended_attention
```

## 8.4 Status Model

最低限の状態は次の 3 段階を推奨する。

```text
NORMAL
WATCH
WARNING
```

必要に応じて将来拡張。

```text
CRITICAL
```

ただし初期設計では過剰に細分化しない。

## 8.5 Runtime Rule

- 単一指標だけで WARNING にしない
- watchpoints と signal を必ず接続する
- headline は簡潔にする
- 理由のない alert を禁止する
- daily run ごとの比較可能性を重視する

重要原則

```text
Early Warning は怖がらせるためではなく見落としを減らすためにある
```

---

# 9. Output Artifacts

Prediction Runtime の出力は次の場所に固定する。

```text
analysis/prediction/
```

最低成果物

```text
analysis/prediction/signal_latest.json
analysis/prediction/scenario_latest.json
analysis/prediction/prediction_latest.json
analysis/prediction/early_warning_latest.json
```

補助成果物候補

```text
analysis/prediction/runtime_status.json
analysis/prediction/prediction_bundle_latest.json
analysis/prediction/watchpoints_latest.json
```

重要原則

```text
latest 系は UI と運用の入口である
```

---

# 10. Prediction History Freeze

Prediction は

```text
日次仮説
```

として凍結保存される。

保存先は次で固定する。

```text
analysis/prediction_history/
```

または現行 UI 実装整合のために

```text
analysis/prediction/history/
```

を利用する場合は、
どちらか一方を正式仕様として固定し、UI 依存箇所を必ず一致させる。

## 10.1 Purpose

- 予測検証
- バックテスト
- 研究ログ
- drift 監視
- 「その日どう見ていたか」の証跡保存

## 10.2 Freeze Unit

凍結単位は原則として日次。

例

```text
prediction_2026-03-09.json
scenario_2026-03-09.json
signal_2026-03-09.json
early_warning_2026-03-09.json
```

## 10.3 Rule

- latest を上書きしてよい
- history は上書きしない
- freeze は再現可能な日付キーを持つ
- future backtest のため summary だけでなく理由も保存する

重要原則

```text
Prediction History は研究資産である
```

---

# 11. Morning Ritual Integration

Prediction Runtime は

```text
scripts/run_morning_ritual.ps1
```

の終盤で実行される。

理想実行順は次のとおり。

```text
Fetch
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
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction
↓
Early Warning
↓
Prediction History Freeze
↓
UI Publish
```

## 11.1 Integration Rule

- Morning Ritual 完了前に Prediction latest を確定する
- Prediction latest 確定後に history を凍結する
- UI publish は latest を読むだけにする
- Morning Ritual の失敗時は部分成果物を明示する

## 11.2 Heartbeat Rule

Prediction Runtime は常時推論エンジンではなく

```text
日次心拍の更新仮説エンジン
```

として扱う。

重要原則

```text
Prediction は Morning Ritual によって毎日更新される仮説である
```

---

# 12. UI Integration

UI は Prediction Runtime の成果物を **read-only** で参照する。

Prediction UI の主入力

```text
analysis/prediction/prediction_latest.json
analysis/prediction/scenario_latest.json
analysis/prediction/early_warning_latest.json
```

Prediction History UI の主入力

```text
analysis/prediction_history/
```

または正式採用した history ディレクトリ。

## 12.1 UI Role

UI の役割は以下に限定する。

- summary を表示する
- overall_risk を表示する
- dominant_scenario を表示する
- confidence を表示する
- watchpoints を表示する
- early warning status を表示する
- history を閲覧可能にする

## 12.2 UI Forbidden

UI 側で以下は禁止。

- scenario を再計算する
- risk を再判定する
- confidence を再計算する
- watchpoints を勝手に並び替えて意味変更する

重要原則

```text
UI は prediction logic を持たない
```

---

# 13. Failure Safety

Prediction Runtime は日次運用のため、
部分失敗時の振る舞いを明確にする。

## 13.1 Failure Cases

### Case 1: Signal build failure

- scenario build を停止する
- prediction build を停止する
- runtime_status に失敗理由を残す
- 前日 latest の無言流用はしない

### Case 2: Scenario build failure

- prediction build を停止する
- early warning を暫定生成しない
- UI に stale data を出す場合は stale 明示が必要

### Case 3: Prediction build failure

- signal / scenario を残して失敗を記録する
- history freeze を停止する

### Case 4: History freeze failure

- latest は生成済みでも runtime warning を記録する
- 研究ログ欠損として扱う

## 13.2 Safety Principles

```text
失敗を隠さない
```

```text
古い prediction を新しい prediction のふりをしない
```

```text
部分成功と完全成功を区別する
```

---

# 14. Runtime Status and Observability

Prediction Runtime は自分自身の状態も観測可能にする。

推奨成果物

```text
analysis/prediction/runtime_status.json
```

想定項目例

```text
as_of
status
steps_completed
steps_failed
input_checks
output_checks
duration_ms
notes
```

これにより

- Morning Ritual の末尾で確認しやすい
- Prediction 系だけの失敗を切り分けやすい
- UI / deploy 前に整合確認できる

重要原則

```text
Prediction Runtime も観測対象にする
```

---

# 15. Minimal Runtime Contract

Prediction Runtime の最低契約をここで固定する。

## 15.1 Input Contract

```text
trend_latest.json が存在すること
health_latest.json が読めること
as_of を取得できること
```

## 15.2 Output Contract

```text
signal_latest.json
scenario_latest.json
prediction_latest.json
early_warning_latest.json
```

が生成されること。

## 15.3 Freeze Contract

```text
prediction history に日付付き成果物が保存されること
```

## 15.4 UI Contract

```text
UI は latest を読むだけで主要表示が成立すること
```

---

# 16. Future Expansion

Prediction Runtime は将来以下へ拡張可能である。

- multi-horizon prediction
- weekly scenario rollup
- historical analog matching
- prediction drift detection
- pair-specific risk prediction
- domain-specific scenario trees
- decision support agent

ただし初期段階では複雑化しすぎない。

重要原則

```text
まずは日次で安定し、あとで拡張する
```

---

# 17. Final Runtime Principle

Prediction Runtime を一言で言うと次である。

```text
Signal から Scenario を作り、Scenario から Prediction を作り、Prediction を日次仮説として凍結する心拍エンジン
```

GenesisPrediction において重要なのは

```text
単発予測ではなく
説明可能な危険分岐の継続監視
```

である。

そのため Prediction Runtime は

- 観測を飛ばさない
- Trend を飛ばさない
- Signal を飛ばさない
- Scenario を飛ばさない
- Prediction を主役にしない
- Early Warning を運用可能にする
- History を研究資産として残す

という原則の上で動く。

---

# 18. Final Summary

GenesisPrediction v2 の Prediction Runtime は次の流れで固定する。

```text
Trend
↓
Signal
↓
Scenario
↓
Prediction
↓
Early Warning
↓
History Freeze
↓
UI
```

重要なのは

```text
Prediction を当てものにしないこと
```

である。

Prediction Runtime は

```text
危険を早く知るための説明可能な未来分岐運用エンジン
```

として設計する。

---

END OF DOCUMENT
