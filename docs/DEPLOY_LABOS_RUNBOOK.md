# DEPLOY_LABOS_RUNBOOK

GenesisPrediction v2 / LABOS 公開用 Deploy 手順（商用品質）

## 目的
- 公開環境で `/static` と `/analysis` が配信されることを確認する
- FX Multi Overlay v1 の必須 URL が生きていることを確認する

## 重要ルール
- deploy は **再実行可能**であること（失敗しても壊さない）
- 公開は **static hosting** として扱い、生成物をそのまま配信する
- 作業は **自宅PCのみ**

---

## 1) 前提（ローカル）
- `git status` がクリーン
- 朝の儀式（FX）を回して最新の overlay が生成済み
  - `scripts/run_daily_fx_rates.ps1`
  - `scripts/run_daily_fx_inputs.ps1`
  - `scripts/run_daily_fx_overlay.ps1`

---

## 2) 公開パッケージ作成（ローカル）
