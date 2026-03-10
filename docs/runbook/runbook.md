# Runbook — GenesisPrediction v2
（2026-02-16 固定版：Morning Ritual 正式採用 / 差分追加禁止）

---

## 0. 目的

GenesisPrediction v2 は、**未来を決めるシステムではない**。

これは「世界の変化を冷静に観測し続けるための装置」である。

- 判断は常に人間が行う
- 当日速報は扱わない（前日確定主義）
- STOP は最後の手段
- Data Health は監査装置であり、自然に OK へ収束する設計とする

---

## 1. 基本原則

- 生成物（JSON / PNG / HTML）が正本（SST）
- GUI は正本を読むだけ（read-only）
- 手動修正は禁止
- WARN は設計で消す
- 対処療法は禁止
- 自然治癒設計を採用する

---

## 2. 全体構成（役割分離）

### 自動処理
- events
- anchors
- analogs
- daily_news
- sentiment
- daily_summary
- fx_overlay
- health

### GUI
- 正本を読むだけ
- 推測しない
- HTML解析しない

### 人間
- 1行 reflection を残す
- 数値を盲信しない

### docs (.md)
- 判断の記録
- 設計の固定

---

## 3. 日次正式ルーチン（唯一の入口）

## 3.1 Morning Ritual（正式）

毎朝はこれだけ実行する：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Guard

powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-16


5. GUI運用原則（SST固定）

GUI は正本を読むのみ

JSONを再構築しない

HTMLを解析して推測しない

SST外の推論禁止

6. Data Health 方針

OK=10 / WARN=0 / NG=0 を基準とする

missing は設計で消す

手動コピーで消さない

構造に組み込む

7. 変更ルール（凍結）

差分追加（部分修正・パッチ方式）禁止

必ず完全ファイル全文で提示

1ターン = 1作業

git diff 確認 → commit → push

壊れたら即 restore

8. 人間の役割

数値を信じすぎない

過去の判断と照合する

reflection を1行で残す

迷ったら止まる

9. 最終原則

GenesisPrediction は予言装置ではない。
これは「冷静さを保つための観測装置」である。

