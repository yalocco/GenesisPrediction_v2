# Prediction Layer Design
GenesisPrediction v2

Status: Active  
Purpose: Signal / Scenario / Prediction を統合する Prediction Layer の中核設計を固定する  
Last Updated: 2026-03-09

---

# 1. Purpose

Prediction Layer は

Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction

という流れの後半を担う。

GenesisPrediction において Prediction は主役ではない。
主役は

- Observation
- Trend
- Signal
- Scenario

であり、Prediction はそれらを人間が扱える形にまとめる最終要約である。

この文書の目的は次を固定することである。

- Signal Layer の役割
- Scenario Layer との接続
- Prediction Layer の責務
- Early Warning Engine の位置づけ
- 出力形式
- Morning Ritual / UI / History への統合

---

# 2. Design Position in GenesisPrediction

GenesisPrediction v2 の基本構造は次の通りである。

Data Sources
↓
scripts
↓
analysis (Single Source of Truth)
↓
Prediction Layer
↓
UI
↓
LABOS

重要原則

- analysis が唯一の真実である
- Prediction Layer は analysis を読むだけである
- UI は Prediction を表示するだけである
- Prediction は再計算を UI 側に持ち込まない

Prediction Layer は Runtime SST 上の成果物を使って、
未来の危険分岐を整理し、
公開可能な予測要約へ変換する層である。

---

# 3. Core Design Principle

Prediction Layer の設計原則を一言で言うと

```text
Explainable branching over single-shot prediction
```

である。

つまり

- 単発予測より説明可能な未来分岐を優先する
- 単一未来を前提にしない
- 人間の判断支援を目的にする
- 危険を早く知ることを優先する

重要原則

```text
Scenario を挟まない Prediction は採用しない
```

Prediction が直接 Observation や Trend から飛び出す構造は避ける。
必ず Signal と Scenario を通過させる。

---

# 4. Layer Responsibilities

Prediction Layer の責務分離は以下で固定する。

## Observation

観測データを揃える層。

例

- daily summary
- sentiment
- digest
- overlay
- health

## Trend

変化の方向を抽出する層。

例

- rising
- falling
- stable
- accelerating

## Signal

注意すべき兆候を検出する層。

例

- persistence
- acceleration
- reversal
- anomaly
- regime_shift
- volatility_expansion

## Scenario

Signal を材料として未来分岐を整理する層。

例

- best_case
- base_case
- worst_case

## Prediction

公開用の最終要約を生成する層。

例

- overall_risk
- dominant_scenario
- confidence
- summary
- watchpoints
- drivers

重要原則

```text
各層の責務を混ぜない
```

---

# 5. Signal Layer Role

Signal Layer は Trend の中から

```text
今は注意すべき変化が起きているか
```

を検出する。

Trend が「流れ」を表すのに対し、
Signal は「警戒すべき兆候」を表す。

Signal Layer の目的

- 平常変化と警戒変化を分ける
- Scenario Engine に入力するための異常点を抽出する
- Early Warning Engine の一次入力を作る

Signal はまだ未来予測ではない。
Signal は

```text
未来を変えうる兆候
```

である。

---

# 6. Signal Output Design

Signal Layer の最小成果物は

```text
analysis/prediction/signal_latest.json
```

である。

最小構成

```text
as_of
horizon
signals[]
summary
engine_version
source_refs
```

signals[] の各要素が持つべき最低項目

```text
signal_id
signal_type
severity
confidence
direction
summary
related_trends
drivers
watchpoints
invalidation_conditions
```

## signal_type の基本分類

```text
persistence
acceleration
reversal
anomaly
regime_shift
volatility_expansion
```

## severity

Signal の危険度。

例

```text
low
medium
high
critical
```

## confidence

confidence は

```text
当たる確率
```

ではない。

意味は

```text
現在の観測とその Signal 解釈の整合性の強さ
```

である。

## drivers

Signal を支える要因。

## watchpoints

その Signal が継続・悪化・反転するかを見極める観測点。

## invalidation_conditions

何が起きたらその Signal 解釈を見直すべきか。

---

# 7. Early Warning Engine

Early Warning Engine は独立した別世界の層ではなく、
Signal Layer と Prediction Layer の間をつなぐ運用エンジンとして位置づける。

役割

- Signal の中から即時注意対象を抽出する
- 人間に見せるべき警戒項目を短く要約する
- Scenario 更新が必要かどうかを判定する
- Prediction summary の alert 部分を生成する

Early Warning Engine の入力

- trend_latest.json
- signal_latest.json
- 直近 history
- health / overlay / digest の要約情報

Early Warning Engine の出力

- early_warning_level
- early_warning_summary
- triggered_watchpoints
- escalated_signals
- scenario_update_required

重要原則

```text
Early Warning は Prediction の代替ではない
```

Early Warning は

- 早く気づくための短い警告
- Scenario と Prediction を更新するための入口

として扱う。

---

# 8. Scenario to Prediction Conversion

Scenario Engine は複数の未来分岐を生成する。
Prediction Engine はそれを

```text
公開用の統合要約
```

へ変換する。

この変換で行うこと

- dominant_scenario の決定
- overall_risk の評価
- summary の生成
- watchpoints の統合
- drivers の統合
- scenario_probabilities の整形
- early_warning の添付

Prediction は Scenario を潰して一本線にするのではない。
Prediction は

```text
主要分岐を残したまま人間が理解しやすい形に圧縮する
```

ための層である。

重要原則

```text
Prediction は Scenario の上位要約であり、Scenario の代替ではない
```

---

# 9. Prediction Layer Role

Prediction Layer の役割は次の三つに固定する。

## 1. 最終要約

Signal と Scenario を公開可能な文章・指標へ変換する。

## 2. 判断支援

何を注視すべきかを watchpoints と drivers で示す。

## 3. 危険分岐の早期提示

Early Warning を通じて、
重大な悪化分岐が見え始めた時点で注意を出す。

Prediction Layer は

```text
未来を断言するための層
```

ではなく、

```text
危険分岐を早く見せるための層
```

である。

最終決定は Human が行う。

---

# 10. Prediction Output Design

Prediction Layer の最小成果物は

```text
analysis/prediction/prediction_latest.json
```

である。

最小構成

```text
as_of
horizon
overall_risk
dominant_scenario
confidence
summary
early_warning
watchpoints
drivers
scenario_probabilities
invalidation_conditions
engine_version
source_refs
```

## overall_risk

全体の危険度。

例

```text
low
guarded
elevated
high
critical
```

## dominant_scenario

現時点でもっとも整合的な Scenario。

例

```text
best_case
base_case
worst_case
```

## confidence

Prediction 全体の確信度。

意味は

```text
現在の観測、Trend、Signal、Scenario の整合性の強さ
```

である。

## summary

人間向けの短い要約。

## early_warning

即時警戒が必要な要素。

## scenario_probabilities

各シナリオの相対的重み。

例

```text
best_case: 0.20
base_case: 0.55
worst_case: 0.25
```

v1 では厳密な統計確率よりも

```text
相対比較としての重み
```

を優先してよい。

## invalidation_conditions

何が起きたら Prediction を再評価すべきか。

---

# 11. Explainability Requirements

Prediction は必ず説明可能でなければならない。

最低限必要な要素

- summary
- drivers
- watchpoints
- confidence
- invalidation_conditions

理由のない予測は採用しない。

説明可能性の目的

- 人間が使える
- 後で検証できる
- Prediction History と比較できる
- 外れた時に原因分析できる

重要原則

```text
当たったかどうかだけではなく、なぜそう見えたかを保存する
```

---

# 12. Prediction Horizon

Prediction は horizon を持つ。

標準 horizon

```text
3d
7d
30d
```

意味

```text
3d  = short-term
7d  = tactical outlook
30d = structural outlook
```

v1 の標準は

```text
7d
```

とする。

理由

- digest / sentiment / overlay の更新周期と合わせやすい
- Morning Ritual の日次更新と整合する
- 短すぎず長すぎず、運用しやすい

将来は multi-horizon 化を可能にするが、
初期設計では 7d を標準として固定する。

---

# 13. Storage Structure

Prediction Layer の保存場所は次で固定する。

```text
analysis/prediction/
```

基本成果物

```text
trend_latest.json
signal_latest.json
scenario_latest.json
prediction_latest.json
```

将来の履歴拡張

```text
trend_history.json
signal_history.json
scenario_history.json
prediction_history.json
```

日次凍結保存

```text
analysis/prediction_history/
```

Prediction は

```text
日次仮説
```

として保存される。

これにより可能になること

- バックテスト
- 予測検証
- ドリフト観測
- 改良前後比較

---

# 14. Morning Ritual Integration

Prediction Layer は Morning Ritual の一部として毎日更新される。

理想的な流れ

```text
fetch
↓
analysis build
↓
observation memory save
↓
trend build
↓
signal build
↓
scenario build
↓
prediction build
↓
prediction memory save
↓
prediction history index build
↓
UI update
```

重要原則

```text
Prediction は日次心拍で更新される仮説
```

Prediction Layer は Morning Ritual の最後に付け足されるおまけではない。
Observation から続く自然な連鎖として組み込む。

---

# 15. UI Integration

UI は次を参照する。

```text
analysis/prediction/prediction_latest.json
```

必要に応じて以下も参照する。

```text
analysis/prediction/signal_latest.json
analysis/prediction/scenario_latest.json
analysis/prediction_history/
```

UI の役割

- 表示のみ
- 再計算しない
- read-only

Prediction UI の最低表示項目

- summary
- overall_risk
- dominant_scenario
- confidence
- early_warning
- watchpoints
- drivers
- scenario probabilities

Prediction History UI の役割

- 過去 Prediction の比較
- 日次仮説の検証
- 後知恵との差分確認

---

# 16. LABOS Integration

Prediction Layer の出力は将来の LABOS 公開 UI でも利用される。

例

- global risk outlook
- weekly risk summary
- alert indicators

そのため Prediction は

```text
公開可能な形式
```

で設計する。

公開時の原則

- summary は短く明確にする
- watchpoints は運用可能な表現にする
- drivers は説明責任を果たせる粒度にする
- confidence は飾り値にしない

---

# 17. Non-Goals

Prediction Layer がやらないことも明確にする。

やらないこと

- 単一未来の断言
- UI 内での再推論
- 説明不能なスコアだけの出力
- Human の意思決定の代行
- Signal を飛ばして Scenario を作ること
- Scenario を飛ばして Prediction を出すこと

重要原則

```text
Prediction は意思決定装置ではなく判断支援装置である
```

---

# 18. v1 Fixed Scope

今回の v1 で固定する範囲

- Signal Layer の責務固定
- Early Warning Engine の位置づけ固定
- Scenario → Prediction 変換ルール固定
- prediction_latest.json の最小構造固定
- horizon = 7d の採用
- Morning Ritual 連携方針固定
- UI read-only 原則固定

v1 で保留とするもの

- multi-horizon 本格対応
- historical analog matching の本統合
- scenario tree の深層化
- prediction drift detection の本格実装
- 自動スコア最適化

---

# 19. Final Summary

GenesisPrediction の Prediction Layer は

Observation
↓
Trend
↓
Signal
↓
Scenario
↓
Prediction

で構成される。

重要なのは

```text
Prediction を主役にしない
```

ことである。

主役は

```text
Observation
Trend
Signal
Scenario
```

であり、
Prediction はその最終要約である。

Signal は注意すべき兆候を捉え、
Scenario は未来分岐を整理し、
Prediction はそれを人間に使える形へ圧縮する。

Early Warning Engine はこの流れの中で

```text
危険を早く知るための運用エンジン
```

として機能する。

この設計により GenesisPrediction は

- 単発の当てものAI
- 理由のないスコアAI
- UI 側で再推論する危険な構造

を避け、

```text
危険を早く知るための説明可能な予測システム
```

として進化できる。

---

END OF DOCUMENT
