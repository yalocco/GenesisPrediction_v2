# Prediction Runtime
GenesisPrediction v2

Status: Active
Purpose: Prediction Layer を日次運用へ組み込む Runtime 設計
Last Updated: 2026-03-07

---

# 0. Purpose

このドキュメントは

```text
Prediction Layer を実際に動かす Runtime

を定義する。

目的

Prediction Engine を Morning Ritual に組み込む

実行順序を固定する

生成物を明確にする

失敗時の切り分けを簡単にする

将来の Prediction Pipeline 実装の土台にする

Prediction Layer は設計だけでなく、

毎日安定して再現可能に動くこと

が必要である。

1. Position in Full System

GenesisPrediction v2 の全体構造

data
↓
scripts
↓
analysis
↓
prediction
↓
UI

Runtime 上の実際の意味

data        = 素材
scripts     = 生成装置
analysis    = Runtime SST
prediction  = analysis を元にした未来推定
UI          = 表示

重要原則

analysis = Single Source of Truth
prediction は analysis を入力として生成される
UI は prediction を読むだけ
UI は再計算しない
2. Prediction Runtime Overview

Prediction Runtime は次の処理を行う。

analysis/latest を読む
↓
Trend Engine 実行
↓
Signal Engine 実行
↓
Scenario Engine 実行
↓
Prediction Engine 実行
↓
analysis/prediction/* を更新

Prediction Runtime は

Morning Ritual 完走後

に実行される。

理由

Prediction は analysis を入力にするため

upstream の fetch / analyzer / digest / fx / health が揃ってから動くべきため

SST が確定した後に future layer を生成するため

3. Runtime Order in Morning Ritual

Prediction Runtime を含む全体順序

git pull
↓
run_daily_with_publish
↓
FX lane
↓
build_data_health
↓
latest artifacts refresh
↓
Prediction Runtime
↓
GUI確認

Prediction Runtime の位置は

latest artifacts refresh の後
GUI確認の前

で固定する。

理由

Prediction は最新 analysis を使う

GUI は prediction 出力を表示対象に含みうる

GUI確認時には prediction_latest.json が存在しているべき

4. Prediction Runtime Internal Flow

Prediction Runtime の内部フロー

1. Load analysis inputs
2. Validate required files
3. Build trend_latest.json
4. Build signal_latest.json
5. Build scenario_latest.json
6. Build prediction_latest.json
7. Write latest outputs
8. Optional history snapshot

正式フロー

analysis/*
↓
Trend Engine
↓
analysis/prediction/trend_latest.json
↓
Signal Engine
↓
analysis/prediction/signal_latest.json
↓
Scenario Engine
↓
analysis/prediction/scenario_latest.json
↓
Prediction Engine
↓
analysis/prediction/prediction_latest.json
5. Runtime Entry Point

Prediction Runtime の公式 entrypoint は
将来的に以下を想定する。

scripts/run_prediction_pipeline.py

役割

Prediction Layer 全体の orchestrator

入力確認

各 engine 実行

出力保存

ログ出力

失敗時の終了コード返却

このファイルは

Morning Ritual から呼ばれる prediction 専用ランナー

である。

6. Expected Inputs

Prediction Runtime の主入力は以下。

analysis/world_politics/sentiment_latest.json
analysis/world_politics/daily_summary_latest.json
analysis/health_latest.json
analysis/fx/*
analysis/digest/*

将来追加される可能性

analysis/history/YYYY-MM-DD/*
analysis/prediction/history/*
observation memory outputs
trend helper datasets

入力の原則

Prediction は data/ を直接見ない
Prediction は analysis を正として使う
7. Required Input Validation

Prediction Runtime 開始時に最低限確認すべきもの

analysis directory exists
required latest files exist
JSON parse succeeds
as_of / date fields are usable
critical inputs are not empty

最低限の required files 例

analysis/world_politics/sentiment_latest.json
analysis/world_politics/daily_summary_latest.json

補助扱いにできる入力

analysis/health_latest.json
analysis/fx/*
analysis/digest/*

原則

必須入力が欠けたら hard fail

補助入力が欠けたら warn + degraded run 可

8. Output Files

Prediction Runtime が生成する正式成果物

analysis/prediction/trend_latest.json
analysis/prediction/signal_latest.json
analysis/prediction/scenario_latest.json
analysis/prediction/prediction_latest.json

必要に応じて追加可能な付随成果物

analysis/prediction/runtime_status_latest.json
analysis/prediction/prediction_health_latest.json
analysis/prediction/prediction_debug_latest.json

ただし v1 では複雑化を避けるため、
まずは core 4 files を最優先とする。

9. Optional History Snapshot

Prediction Runtime は将来的に history 保存を行ってよい。

保存先例

analysis/prediction/history/YYYY-MM-DD/
  trend.json
  signal.json
  scenario.json
  prediction.json

保存タイミング

prediction_latest.json 生成成功後

原則

latest 成功後に history 保存

history 失敗で latest を壊さない

latest の生成が主目的

history は追加価値

10. Runtime Success Criteria

Prediction Runtime 成功条件

trend_latest.json が生成されている
signal_latest.json が生成されている
scenario_latest.json が生成されている
prediction_latest.json が生成されている
JSON が parse 可能
prediction summary が空でない
overall_risk が設定されている
working tree を汚さない

Morning Ritual 視点の成功条件

Prediction Layer が安定生成され
GUI確認前に prediction_latest.json が存在する
11. Failure Handling Policy

Prediction Runtime の異常時方針

11.1 Input missing

例

sentiment_latest.json missing
daily_summary_latest.json missing

対応

hard fail
Prediction Runtime 停止
原因をログ出力

理由

Prediction は analysis を前提とするため、
核心入力欠落のまま進めない。

11.2 Optional domain missing

例

fx input missing
health input missing
digest input missing

対応

warn
degraded mode で継続可

理由

Prediction v1 は world_politics 主体でも成立しうるため。

11.3 Engine-level failure

例

trend build failed
scenario JSON write failed

対応

どの step で止まったか明示
partial write を避ける
非正常終了コードを返す

原則

壊れた prediction_latest.json を残さない
12. Logging Design

Prediction Runtime は step-based logging を持つ。

推奨ログ例

[Prediction] START
[Prediction] Validate inputs
[Prediction] Build trend
[Prediction] Build signal
[Prediction] Build scenario
[Prediction] Build prediction
[Prediction] Write outputs
[Prediction] DONE

エラー時例

[Prediction] ERROR at Build scenario
reason: missing signal collection

ログ原則

step 名が分かる

入出力の失敗箇所が明確

Morning Ritual から読んで追跡しやすい

13. Runtime Idempotency

Prediction Runtime は

同じ入力なら同じ出力

を原則とする。

つまり

再実行しても prediction が不必要に揺れない

ことを目指す。

重要性

デバッグが容易

backtest が可能

信頼性が上がる

日次運用で安心して再実行できる

14. Runtime Isolation

Prediction Runtime は
既存の analysis 生成処理と責務を分離する。

原則

run_daily_with_publish は観測層まで
run_prediction_pipeline.py は予測層のみ

これにより

デバッグしやすい

失敗箇所が明確

将来 Prediction だけ再実行できる

Morning Ritual の構造がきれいになる

15. Recommended Script Structure

将来の推奨構成

scripts/
  run_prediction_pipeline.py
  build_trend.py
  build_signal.py
  build_scenario.py
  build_prediction.py

役割

run_prediction_pipeline.py = orchestrator
build_trend.py             = trend generator
build_signal.py            = signal generator
build_scenario.py          = scenario generator
build_prediction.py        = final prediction generator

v1 では 1 file orchestrator + internal functions でもよい。

16. CLI Design

推奨 CLI 例

python scripts/run_prediction_pipeline.py --date 2026-03-07

オプション例

--date YYYY-MM-DD
--write-history
--strict
--debug

意味

--date = 対象日

--write-history = history snapshot 保存

--strict = optional input 欠損も fail 扱い

--debug = 詳細ログ出力

v1 では最小構成で始めてよい。

17. Morning Ritual Integration Example

将来の Morning Ritual での呼び出し例

python scripts/run_prediction_pipeline.py --date (Get-Date -Format "yyyy-MM-dd")

PowerShell 化する場合の候補

scripts/run_prediction_pipeline.ps1

ただし中核処理は Python 側に集約するのが望ましい。

理由

JSON 操作に強い

ロジック分離しやすい

backtest / reuse がしやすい

18. Prediction Health Concept

将来的に Prediction Layer 専用 health を持ってよい。

例

prediction input completeness
trend build status
signal count sanity
scenario probability sum check
prediction summary presence

保存候補

analysis/prediction/prediction_health_latest.json

ただし v1 では必須ではない。
まずは core pipeline 成功を優先する。

19. Runtime Validation Rules

Prediction Runtime 完了時の最低 validation

trend_latest.json
domains が存在する
最低1件以上の trend entry がある
signal_latest.json
signals array が存在する
空でもよいが JSON 構造は正しい
scenario_latest.json
best/base/worst のいずれかが存在する
probability が使える
prediction_latest.json
overall_risk がある
summary が空でない
watchpoints が配列
dominant_scenario が設定されている
20. Runtime Philosophy

Prediction Runtime の最重要思想

観測の上に未来推定を積む

である。

つまり

Prediction は analysis の後段である

Prediction は analysis を壊さない

Prediction は UI で計算しない

Prediction は毎日同じ順序で生成する

これは GenesisPrediction の全体思想

速度より再現性

と一致する。

21. Phase Strategy

Prediction Runtime の段階導入

Phase 1
trend / signal / scenario / prediction latest のみ生成
Phase 2
history snapshot 追加
Phase 3
prediction health / debug artifacts 追加
Phase 4
multi-horizon support
Phase 5
backtest / drift detection / alert hooks

最初から全部やらず、
動く最小構成で入れる。

22. Final Role

Prediction Runtime は

Prediction Layer の心拍

である。

Observation System が

世界を観測する

なら、

Prediction Runtime は

その観測から未来推定を毎日生成する

役割を持つ。

これにより GenesisPrediction は

世界観測AI
↓
未来予測AI

へ実際に進化する。

END OF DOCUMENT