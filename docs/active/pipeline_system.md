# Pipeline System (GenesisPrediction v2)
Version: 1.0
Status: Draft -> Active
Last Updated: 2026-03-05

## 0. 目的
GenesisPrediction v2 の “生成の流れ” を固定化し、
- 何を回すと
- 何が生成され
- UIは何を読むのか
をスレ非依存で復元できるようにする。

## 1. パイプラインの大原則
- 真実（SST）は analysis/ のみ
- scripts / docker は SST（analysis）を作る工場
- GUIは analysis を読むだけ（生成しない）
※SST定義の公式は docs/repo_map.md を参照

## 2. 毎日運用の標準（Morning Ritual）
標準手順は docs/runbook_morning.md を正とする（この文書は概要＋地図）。

概略:
1) git pull（clean確認）
2) run_daily_with_publish
3) FX lane
4) Data Health 更新
5) GUI確認
6) 必要時のみDeploy

## 3. フロー図（概略）

### 3.1 Main lane
git pull
↓
scripts/run_daily_with_publish.ps1
↓
(fetcher / analyzer / viewmodel生成)
↓
analysis/world_politics/*_latest.json など（SST）

### 3.2 FX lane
scripts/run_daily_fx_rates.ps1
↓
scripts/run_daily_fx_inputs.ps1
↓
scripts/run_daily_fx_overlay.ps1
↓
analysis/fx/*.png / *.csv / *_latest.json（SST）

### 3.3 Health lane
scripts/build_data_health.py
↓
analysis/**/health_latest.json（SST）

## 4. 生成物（SST）カテゴリ一覧（育成枠）
※ここは “確定したら追記” する。最初はカテゴリのみ固定。

- World Politics
  - daily_news_latest.json
  - daily_summary_latest.json
  - sentiment_latest.json
  - view_model_latest.json（存在する場合）

- Digest
  - digest系 view_model_latest.json
  - highlights / KPI / thumbnails 用の派生JSON（存在する場合）

- FX
  - fx_overlay_latest.png
  - dashboard CSV
  - remittance判断の view_model（存在する場合）

- Health
  - health_latest.json

## 5. 異常時の一次切り分け（超短縮）
- GUIが崩れた → まず analysis を確認（SSTが正しいか）
- 数値が出ない → view_model / summary / sentiment の生成状況を見る
- ALL_ZERO → sentiment生成/入力データ破損を疑う
※詳細ルールは docs/runbook_morning.md を参照

## 6. TODO（今後追記）
- 各 script の入力/出力ファイル（analysis側）を “確定表” として列挙
- dated成果物（YYYY-MM-DD）と latest alias の規約を明文化
- Deploy lane（公開）の手順を別runbookとして切り出す（必要になったら）