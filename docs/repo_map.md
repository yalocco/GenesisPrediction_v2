# GenesisPrediction v2 --- Repository Map

Status: Active Last Updated: 2026-03-08 Purpose: Repository
の責務分離を公式定義する

------------------------------------------------------------------------

# 0. Purpose

このドキュメントは

GenesisPrediction v2 の

**Repository 構造と責務**

を固定する。

目的

-   新しいAIが repo 構造を誤解しないようにする
-   scripts / data / analysis / UI の責務分離を明確にする
-   デバッグ時の判断を速くする
-   Repository Memory の基盤とする

------------------------------------------------------------------------

# 1. Repository Top Structure

GenesisPrediction v2 の基本構造

    scripts/
    data/
    analysis/
    app/
    docs/

それぞれの役割は明確に分離されている。

------------------------------------------------------------------------

# 2. scripts

    scripts/

役割

    データ生成
    パイプライン実行
    分析処理
    レポート生成

scripts は

    工場

である。

ここでは

    データを生成する

だけであり、

    真実は保持しない

------------------------------------------------------------------------

## 2.1 Main Entry

最重要エントリーポイント

    scripts/run_morning_ritual.ps1

これは

    GenesisPrediction の心拍

である。

------------------------------------------------------------------------

# 3. data

    data/

役割

    素材データ

例

    raw news
    api data
    intermediate data

data は

    再生成可能

である。

------------------------------------------------------------------------

# 4. analysis

    analysis/

analysis は

    Single Source of Truth

である。

つまり

    GenesisPrediction の真実

は

    analysis

にある。

------------------------------------------------------------------------

## 4.1 主な成果物

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

------------------------------------------------------------------------

# 5. app

    app/

役割

    UI

UI は

    analysis を読むだけ

である。

UI は

    read-only

であり、

    分析ロジックを持たない

------------------------------------------------------------------------

## 5.1 UI Location

    app/static/

主なページ

    index.html
    overlay.html
    sentiment.html
    digest.html
    prediction.html
    prediction_history.html

------------------------------------------------------------------------

## 5.2 UI Shared Components

    app/static/common/

    header.html
    footer.html
    layout.js

共通スタイル

    app/static/app.css

------------------------------------------------------------------------

# 6. docs

    docs/

役割

    Repository Memory

つまり

    設計思想
    構造定義
    運用ルール

を保存する。

------------------------------------------------------------------------

## 6.1 Core Docs

重要ドキュメント

    genesis_system_map.md
    repo_map.md
    project_status.md

    pipeline_system.md
    ui_system.md
    ui_data_dependencies.md

    genesis_brain.md
    prediction_layer_design_principles.md

    working_agreement.md
    chat_operating_rules.md

------------------------------------------------------------------------

# 7. Debug 原則

トラブル時の確認順

    1 analysis
    2 scripts
    3 UI

理由

    analysis = 真実

------------------------------------------------------------------------

# 8. Repository Philosophy

GenesisPrediction の repo は

    再現可能な研究システム

として設計されている。

そのため

    生成
    保存
    表示
    設計

を分離する。

------------------------------------------------------------------------

# 9. Responsibility Map

    scripts
    生成

    data
    素材

    analysis
    成果物（真実）

    app
    表示

    docs
    設計

------------------------------------------------------------------------

# 10. Development Rules

GenesisPrediction の基本ルール

    1ターン = 1作業
    差分禁止
    完全ファイル
    長文はダウンロード方式
    必要ならZIP

------------------------------------------------------------------------

# 11. Final Summary

GenesisPrediction v2 Repository

    scripts → 生成
    data → 素材
    analysis → 真実
    app → 表示
    docs → 設計

最重要原則

    analysis が Single Source of Truth

------------------------------------------------------------------------

END OF DOCUMENT
