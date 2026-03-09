# GenesisPrediction v2 --- Project Status

Status: Active\
Last Updated: 2026-03-08\
Version: 2.0

------------------------------------------------------------------------

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

**現在のシステム状態**

をまとめる。

目的

-   Repository Memory の入口を提供する
-   新しいAIが現行構造を理解できるようにする
-   システムの進行状況を整理する
-   次フェーズを明確にする

------------------------------------------------------------------------

# 1. Repository Memory

GenesisPrediction v2 は

    Repository Memory

中心で開発される。

AI は以下の docs を前提知識として扱う。

    docs/genesis_system_map.md
    docs/repo_map.md
    docs/project_status.md

    docs/pipeline_system.md
    docs/ui_system.md
    docs/ui_data_dependencies.md

    docs/genesis_brain.md
    docs/prediction_layer_design_principles.md

    docs/working_agreement.md
    docs/chat_operating_rules.md

これにより

    Chat Memory
    ↓
    Repository Memory
    ↓
    Project Knowledge

の構造を実現する。

------------------------------------------------------------------------

# 2. Current System Architecture

GenesisPrediction v2 の現在の構造

    Data Sources
    ↓
    Pipeline (scripts)
    ↓
    Analysis (Runtime SST)
    ↓
    Prediction Layer
    ↓
    UI
    ↓
    LABOS Public UI

最重要原則

    analysis = Single Source of Truth

------------------------------------------------------------------------

# 3. Pipeline Status

現在の Pipeline は

    Morning Ritual

を中心に構成される。

メインエントリーポイント

    scripts/run_morning_ritual.ps1

主な処理

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
    Prediction

Morning Ritual は

    GenesisPrediction の心拍

として毎日実行される。

------------------------------------------------------------------------

# 4. Analysis Layer

analysis は

    Runtime SST

として扱われる。

主な成果物

    analysis/

    daily_news_latest.json
    daily_summary_latest.json
    sentiment_latest.json
    health_latest.json

    view_model_latest.json

    fx_overlay_latest.png

    trend_latest.json
    signal_latest.json
    scenario_latest.json
    prediction_latest.json

    prediction_history/

UI はこの成果物を読む。

------------------------------------------------------------------------

# 5. UI Status

現在の UI ページ

    Home
    Overlay
    Sentiment
    Digest
    Prediction
    Prediction History

UI の場所

    app/static/

UI の共通構造

    header
    footer
    layout.js
    app.css

UI の原則

    UI は read-only
    UI は分析ロジックを持たない
    UI は再計算しない

------------------------------------------------------------------------

# 6. Prediction Layer

Prediction Layer は現在導入済み。

基本構造

    Observation
    ↓
    Trend
    ↓
    Signal
    ↓
    Scenario
    ↓
    Prediction

Prediction の役割

    最終要約
    判断支援

主な出力

    prediction_latest.json

------------------------------------------------------------------------

# 7. Prediction History

Prediction は研究ログとして保存される。

保存場所

    analysis/prediction_history/

用途

    バックテスト
    予測検証
    研究ログ

Prediction は

    日次仮説

として凍結される。

------------------------------------------------------------------------

# 8. FX Overlay System

現在の Overlay 対応通貨ペア

    JPY/THB
    USD/JPY
    USD/THB

表示

    fx_overlay_latest.png

用途

    FX monitoring
    Remittance timing
    Risk observation

------------------------------------------------------------------------

# 9. Digest System

Digest は

    Daily Risk Summary UI

である。

主な表示

    Summary
    KPI
    Highlights
    Articles

データソース

    view_model_latest.json

------------------------------------------------------------------------

# 10. System Stability

現在の状態

    Morning Ritual 安定
    Digest UI 安定
    Overlay 安定
    Prediction Layer 導入済
    Repository Memory 構築中

------------------------------------------------------------------------

# 11. Current Development Phase

現在のフェーズ

    Repository Memory 整合化

目的

    docs を現行構造へ合わせる
    新AIが誤解しないようにする

更新対象

    genesis_system_map.md
    ui_system.md
    project_status.md
    repo_map.md

------------------------------------------------------------------------

# 12. Next Phase

次のフェーズ

    Prediction System 強化

予定

    Trend detection
    Signal detection
    Scenario generation
    Prediction scoring
    Prediction history analysis

------------------------------------------------------------------------

# 13. Future Direction

GenesisPrediction は将来的に

    Global Risk Observation System

として進化する可能性がある。

構造

    News
    ↓
    Sentiment
    ↓
    Trend Detection
    ↓
    Signals
    ↓
    Scenario
    ↓
    Prediction

目的

    危険を早く知る
    世界の変化を観測する
    判断支援を行う

------------------------------------------------------------------------

# 14. Development Rules

GenesisPrediction の作業ルール

    1ターン = 1作業
    差分提案禁止
    完全ファイル
    長文はダウンロード方式
    必要ならZIP

------------------------------------------------------------------------

# 15. Final Summary

GenesisPrediction v2 は

    Daily Observation System

として設計されている。

中核

    Morning Ritual
    analysis (SST)
    Prediction Layer
    UI Visualization
    Repository Memory

目的

    未来を当てることではなく
    危険を早く知ること

------------------------------------------------------------------------

END OF DOCUMENT
