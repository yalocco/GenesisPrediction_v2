# GenesisPrediction v2
# Morning Runbook（朝の儀式・完全版）
Version: 1.2
Status: Active
Last Updated: 2026-02-19

---

## 0. 目的

本ドキュメントは、GenesisPrediction v2 の「朝の儀式」を固定化するための公式Runbookである。

目的：

- 毎日同じ手順で再現可能にする
- ローカル差異を発生させない
- SST（analysis）を安定生成する
- 研究ログ（予測履歴）を日次で凍結する
- deployとの責務分離を明確にする
- 将来の自分が迷わない構造を作る

朝の儀式は「GenesisPredictionの心拍」である。

途中改造は禁止。
完走が最優先。

---

# 1. 基本原則

1. 完走最優先
2. 途中でコードを書き換えない
3. エラー調査は別スレで行う
4. GUI問題でもまず生成完走を確認
5. 手動でanalysisを書き換えない
6. 研究ログは毎日凍結（ok=falseでも保存）
7. 不安定状態でmainへpushしない

---

# 2. 実行環境

■ 会社PC  
役割：開発・検証・通常実行

■ 自宅PC  
役割：最終確認・deploy専用

原則：
deployは自宅PCのみで実行する。

---

# 3. 朝の儀式 標準フロー

---

## Step 1：最新取得

git pull


確認：

- branch = main
- working tree clean

---

## Step 2：メインパイプライン

powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1


生成内容：

- fetcher
- analyzer
- ViewModel
- scenario
- prediction
- analysis更新

確認：

- エラー無し
- analysis日付更新

---

## Step 3：FX更新

powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_rates.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_inputs.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_overlay.ps1


確認：

- fx_overlay_latest.png 更新
- dashboard CSV 更新

---

## Step 4：Data Health生成

.\.venv\Scripts\python.exe scripts\build_data_health.py --date (Get-Date -Format "yyyy-MM-dd")


確認：

- health.json 更新
- warn数確認（panicしない）

---

## Step 5：研究ログ永続化（Prediction Freeze）

powershell -ExecutionPolicy Bypass -File scripts/run_save_prediction_log.ps1


目的：

- 当日の予測情報を1日1JSONで凍結
- ok=falseでも保存
- 再計算不要の研究資産を蓄積

原則：

- 毎日実行
- 途中停止させない
- analysisと混在させない

---

## Step 6：GUI確認

確認ページ：

- index.html
- overlay.html
- sentiment.html
- digest.html

確認内容：

- 今日の日付表示
- 数値表示
- ALL_ZEROでない
- overlay画像更新済

---

## Step 7：Git状態確認

git status


理想状態：

nothing to commit, working tree clean


必要なら：

git add
git commit
git push


---

## Step 8：Deploy（自宅PCのみ）

Deployは必須ではない。

条件：

- 生成完走済
- GUI正常
- working tree clean
- 安定確認済

会社PCでは実行しない。

---

# 4. 異常時判断

---

## GUI崩れ

1. analysis確認
2. ViewModel確認
3. scriptsログ確認

---

## 数値未表示

1. analysis JSON存在確認
2. run_dailyログ確認
3. data破損疑い

---

## ALL_ZERO

1. sentiment生成確認
2. diagnoseスクリプト実行
3. 元ニュースJSON確認

---

## warn多数

1. health.json確認
2. 古いデータ残留確認
3. 即panicしない

---

## 研究ログ失敗

1. run_save_prediction_log.ps1エラー確認
2. save_prediction_log.py存在確認
3. Python実行確認

---

# 5. 完了条件

朝の儀式成功条件：

- run_daily完走
- FX生成完了
- health更新
- 研究ログ凍結成功
- GUI正常
- git clean

---

# 6. 禁止事項

- 朝の儀式中に仕様変更
- analysis手動編集
- 差分パッチ方式
- 複数作業同時進行
- deployを会社PCで実行

---

# 7. 最終原則

GenesisPredictionは

「思想を持った再現可能システム」

である。

速度より再現性。
拡張より安定。
便利さより構造。

---

END OF DOCUMENT