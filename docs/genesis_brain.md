# Genesis Brain (GenesisPrediction v2)
Version: 1.0
Status: Draft -> Active
Last Updated: 2026-03-05

## 0. 目的
GenesisPrediction v2 の「思想（brain）」を固定化する。
機能やUIの細部ではなく、設計判断の“軸”を残す。

## 1. GenesisPrediction v2 は AI共同開発プロジェクトである
- 人間 + AI が共同で設計・実装・運用する
- そのため「設計思想」「運用ルール」「依存関係」をリポジトリ側に残し、スレ依存を断つ

## 2. 最重要の思想：SST（Single Source of Truth）
- 真実（SST）は analysis/ のみ
- data/ は素材（壊れても再生成できる）
- scripts/ は工場（SSTを生成する）
- GUI（app/static）は表示（読むだけ）

※公式定義は docs/repo_map.md を正とする。

## 3. 責務分離の思想
- scripts/analyzer: 収集・分析・整形・集計（生成）
- analysis: 公開・表示・判断の唯一の成果物（真実）
- app/static: UI（可視化と安全なfallback）
- docs: 迷いをゼロにする“設計の固定化”

## 4. 安定優先（速度より再現性）
- 毎日回すパイプラインは「心拍」
- 完走が最優先。途中で改造しない
- 不安定状態で公開しない

※運用の公式は docs/runbook_morning.md を正とする。

## 5. UI思想（商用品質）
- “派手さ”より “統一感・読みやすさ・壊れない” を優先
- baseline を決め、全ページをそこへ揃える（sentiment baseline）
- 事故防止（ダウンロード運用・freezeタグ・差分禁止）を最優先する

※公式運用は docs/gui_phase2_working_rules.md を正とする。

## 6. 進化の仕方（フェーズ分離）
- GUI改善とデータ改善を混ぜない
- 変更は最小単位でコミットし、安定点にタグ（Freeze）を打つ
- “戻れる” ことが進化の条件

※作業の公式は docs/working_agreement.md を正とする。

## 7. TODO（育成枠）
- 予測（prediction）層の思想（どの層で何を判断するか）
- FX意思決定の原理（UIではなくanalysis/viewmodelとして固定）
- “観測→仮説→検証→凍結” の型を文章化