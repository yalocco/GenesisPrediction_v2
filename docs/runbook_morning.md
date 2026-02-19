# GenesisPrediction v2
# Morning Runbook（朝の儀式）
Version: 1.0
Status: Active
Last Updated: 2026-02-19

---

## 0. 目的

本ドキュメントは、GenesisPrediction v2 の「朝の儀式」を固定化するための公式Runbookである。

目的：

- 毎日同じ手順で再現可能にする
- 迷いをゼロにする
- ローカル差異を発生させない
- SST（analysis）を安定生成する

朝の儀式は聖域であり、途中改造を原則禁止とする。

---

# 1. 基本原則

1. 完走が最優先（途中で改造しない）
2. エラー原因をその場で混ぜない（別スレで対応）
3. GUIが壊れてもまずはデータ生成を完走させる
4. 手動でanalysisを書き換えない

---

# 2. 標準フロー（会社PC / 自宅PC共通）

## Step 1：最新取得

git pull

working tree clean を確認する。

---

## Step 2：メインパイプライン実行

powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1

目的：
- fetcher
- analyzer
- ViewModel生成
- analysis更新

完走が最優先。

---

## Step 3：FX関連更新

powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_rates.ps1  
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_inputs.ps1  
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_overlay.ps1  

目的：
- レート取得
- remittance計算
- overlay PNG生成
- analysis/fx 更新

---

## Step 4：Data Health更新

.\.venv\Scripts\python.exe scripts\build_data_health.py --date (Get-Date -Format "yyyy-MM-dd")

目的：
- health JSON更新
- warn状態の可視化

---

## Step 5：GUI確認

- index.html
- overlay.html
- sentiment.html
- digest.html

確認事項：

- 今日の日付が反映されている
- 数値が表示されている
- overlay画像が更新されている
- ALL_ZEROになっていない

---

## Step 6：必要時のみ Deploy

Deployは必須ではない。

- 安定確認後のみ実行
- 不安定状態で公開しない

---

# 3. 異常時の判断ルール

## 3.1 GUIが崩れた場合

→ まずanalysisを確認  
→ analysisが正しければGUI問題  
→ データが空ならscripts問題

---

## 3.2 数値が出ない

→ analysis内のViewModelを確認  
→ run_dailyログ確認  
→ data破損を疑う

---

## 3.3 ALL_ZEROが出る

→ sentiment生成状況確認  
→ diagnose系スクリプトで確認  
→ data/world_politics破損確認

---

## 3.4 warnが多い

→ health JSON内容確認  
→ 古いデータ残留か確認  
→ 原則：warnは即panicしない

---

# 4. 禁止事項

- 朝の儀式中にコードを書き換える
- エラー調査と機能改善を混ぜる
- analysisを手動編集する
- 不安定状態でpushする

---

# 5. 完了条件

以下が揃えば「朝の儀式成功」とする：

- run_daily完走
- FX overlay生成
- health更新
- GUI正常表示
- working tree clean

---

# 6. 最終原則

朝の儀式は「GenesisPredictionの心拍」である。

毎日同じ動きで、
同じ構造を守り、
SSTを安定生成すること。

速度より再現性。
拡張より安定。

---

END OF DOCUMENT
