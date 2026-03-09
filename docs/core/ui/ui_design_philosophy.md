# UI Design Philosophy

GenesisPrediction v2

Status: Active\
Purpose: Define the fundamental design philosophy for the
GenesisPrediction UI.\
Last Updated: 2026-03-09

------------------------------------------------------------------------

# 0. Purpose

このドキュメントは **GenesisPrediction UI の設計思想** を固定する。

目的:

-   UI設計の判断基準を明確にする
-   AIが勝手にデザイン変更を行うのを防ぐ
-   UI改修時の方向性を統一する
-   長期プロジェクトにおける一貫性を保つ

GenesisPrediction UI は単なるWebデザインではなく

**研究ダッシュボード (Research Dashboard)**

として設計されている。

------------------------------------------------------------------------

# 1. Core Philosophy

GenesisPrediction UI の最重要原則

    Clarity over decoration
    装飾より可読性

目的は

    世界の状況を素早く理解すること

であり、派手さは目的ではない。

------------------------------------------------------------------------

# 2. Dashboard First

GenesisPrediction UI は

    ニュースサイト
    ブログ
    SNS

ではない。

これは

    Observation Dashboard

である。

そのため UI は

-   情報密度
-   読みやすさ
-   状態把握

を最優先する。

------------------------------------------------------------------------

# 3. Stability Over Novelty

UIは頻繁に変えるものではない。

重要原則:

    UIは安定資産

理由:

-   人間はレイアウトを覚える
-   頻繁な変更は認知負荷を生む
-   ダッシュボードは慣れが重要

そのため

    新しいデザイン
    ↓
    既存レイアウトを破壊

は避ける。

------------------------------------------------------------------------

# 4. Single Source of Truth

UIは **データを生成しない**。

原則:

    scripts → analysis を生成
    analysis → Runtime SST
    UI → analysis を読む

つまり

    UIは表示装置

である。

UIで分析ロジックを実装してはいけない。

------------------------------------------------------------------------

# 5. Research Tool Aesthetic

GenesisPrediction UI は

    研究ツール

として設計されている。

デザイン指針:

-   落ち着いたダークテーマ
-   高コントラスト文字
-   カード型レイアウト
-   視線誘導を考慮した構造

派手なアニメーションや装飾は最小限にする。

------------------------------------------------------------------------

# 6. Information Hierarchy

UIは以下の情報階層を守る。

    Global Status
    ↓
    Page Summary
    ↓
    Key Metrics
    ↓
    Content Details
    ↓
    Historical Context

ユーザーは上から順に読むことで

    全体 → 詳細

の理解ができる。

------------------------------------------------------------------------

# 7. Consistency Across Pages

すべてのページは統一された構造を持つ。

共通構造:

    Header
    Global Status
    Hero Section
    Main Content
    Cards
    Timeline / Lists
    Footer

対象ページ:

-   Home
-   Overlay
-   Sentiment
-   Digest
-   Prediction
-   Prediction History

これにより

    どのページでも迷わないUI

を実現する。

------------------------------------------------------------------------

# 8. Component Reuse

UIはコンポーネント再利用を前提とする。

基本コンポーネント:

-   panel
-   card
-   hero
-   status-shell
-   timeline
-   list-stack
-   sparkline

新しいページは

    既存コンポーネントを再利用

すること。

------------------------------------------------------------------------

# 9. Error Tolerance

UIは壊れない設計にする。

想定問題:

-   JSON欠損
-   API停止
-   画像404
-   データ遅延

対策:

    fallback表示
    placeholder
    安全な空状態

UIは

    完全停止してはいけない

------------------------------------------------------------------------

# 10. Performance Awareness

GenesisPrediction UI は

    軽量
    高速
    シンプル

を優先する。

そのため

-   大規模フレームワークは使用しない
-   不要なJavaScriptを避ける
-   静的HTML中心構造

を維持する。

------------------------------------------------------------------------

# 11. Human-Centered Design

GenesisPrediction は

    Human + AI

の共同研究プロジェクトである。

UIの役割:

-   人間が状況を理解する
-   AI分析結果を可視化する
-   判断材料を提示する

最終判断は

    Human

が行う。

------------------------------------------------------------------------

# 12. Commercial Quality Standard

GenesisPrediction UI は

    個人研究プロジェクト

であるが

品質基準は

    商用ダッシュボード品質

を目標とする。

要求水準:

-   読みやすい
-   壊れない
-   一貫したレイアウト
-   高い可視性

------------------------------------------------------------------------

# 13. Long-Term Maintainability

GenesisPrediction は

    10年以上続く研究

を想定している。

そのため UI は

    長期保守可能

である必要がある。

設計指針:

-   シンプルなHTML構造
-   再利用可能コンポーネント
-   明確なデータ依存

------------------------------------------------------------------------

# 14. Final Principle

GenesisPrediction UI の目的は

    情報を美しくすること

ではない。

目的は

    世界の状況を理解すること
    危険信号を早く見つけること
    判断を助けること

である。

------------------------------------------------------------------------

# End of Document
