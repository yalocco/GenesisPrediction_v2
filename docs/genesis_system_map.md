# GenesisPrediction v2 --- System Map

Status: Active\
Purpose: GenesisPrediction v2 の全体構造を1枚で理解できるようにする\
Last Updated: 2026-03-08

------------------------------------------------------------------------

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

**システム全体構造**

を整理するためのマップである。

目的

-   新しいAIが構造を誤解しない
-   開発スレ依存をなくす
-   Repository Memory を自己完結させる
-   GenesisPrediction の責務分離を明確にする

------------------------------------------------------------------------

# 1. GenesisPrediction 全体構造

GenesisPrediction は次のレイヤーで構成される。

Data Sources ↓ Pipeline (scripts) ↓ Analysis (SST) ↓ Prediction Layer ↓
UI ↓ LABOS Public UI

------------------------------------------------------------------------

# 2. Data Sources

観測対象となる外部データ。

例

-   News API
-   MediaStack
-   FX API
-   ExchangeRate

保存先

data/

data は「素材」であり、壊れても再生成できる。

------------------------------------------------------------------------

# 3. Pipeline Layer（scripts）

Pipeline は「生成工場」である。

役割

-   収集
-   分析
-   整形
-   集計

主なエントリーポイント

scripts/run_morning_ritual.ps1

Morning Ritual は GenesisPrediction の心拍である。

Pipeline Flow

Fetch\
↓\
Analyzer\
↓\
Sentiment\
↓\
Digest\
↓\
Overlay\
↓\
Health\
↓\
Prediction

生成物はすべて

analysis/

に出力される。

------------------------------------------------------------------------

# 4. Analysis Layer（SST）

GenesisPrediction の

Single Source of Truth は

analysis/

である。

重要原則

analysis = 真実

UI は analysis を読むだけ。

------------------------------------------------------------------------

# 5. Prediction Layer

Prediction は最終要約。

Observation\
↓\
Trend\
↓\
Signal\
↓\
Scenario\
↓\
Prediction

主な出力

prediction_latest.json

------------------------------------------------------------------------

# 6. Prediction History

保存場所

analysis/prediction_history/

用途

-   研究ログ
-   バックテスト
-   未来検証

Prediction は「日次仮説」として凍結される。

------------------------------------------------------------------------

# 7. UI Layer

UI は Read Only。

場所

app/static/

------------------------------------------------------------------------

## UI Pages

-   Home
-   Overlay
-   Sentiment
-   Digest
-   Prediction
-   Prediction History

------------------------------------------------------------------------

## UI Layout

共通構造

header\
layout.js\
footer

------------------------------------------------------------------------

# 8. Digest UI

Daily Summary UI

表示

-   Summary
-   KPI
-   Highlights
-   Articles

データ

view_model_latest.json

------------------------------------------------------------------------

# 9. Overlay UI

FX 可視化

fx_overlay_latest.png

通貨ペア

-   JPY/THB
-   USD/JPY

------------------------------------------------------------------------

# 10. Sentiment UI

ニュース感情分析

-   positive
-   negative
-   neutral
-   mixed

------------------------------------------------------------------------

# 11. Prediction UI

prediction_latest.json を表示

内容

-   summary
-   risk
-   scenario
-   confidence
-   watchpoints
-   drivers

------------------------------------------------------------------------

# 12. Prediction History UI

過去予測の閲覧

analysis/prediction_history/

用途

-   研究ログ
-   バックテスト
-   検証

------------------------------------------------------------------------

# 13. System Responsibility

data = 素材\
scripts = 生成\
analysis = 成果物（真実）\
UI = 表示\
docs = 設計固定

------------------------------------------------------------------------

# 14. Development Rules

-   1ターン = 1作業
-   差分禁止
-   完全ファイル

------------------------------------------------------------------------

# 15. Final Summary

Data\
↓\
Pipeline\
↓\
Analysis (SST)\
↓\
Prediction\
↓\
UI\
↓\
LABOS

重要原則

analysis が真実\
UI は読むだけ\
Prediction は最終要約\
Morning Ritual は心拍

END OF DOCUMENT
