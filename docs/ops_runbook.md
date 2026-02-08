了解です。**迷いが一切出ない形**で渡します。
下の **1つのコードブロック全体が「1ファイル」**です。

---

## 保存方法（これだけ）

* ファイル名：`docs/ops_runbook.md`
* やること：

  1. 新規ファイルを作る
  2. **下の内容を最初から最後まで全部コピペ**
  3. 保存

---

```md
# GenesisPrediction v2 – Ops Runbook
（運用・復旧・日次実行の公式手順）

---

## 目的

この Runbook は、GenesisPrediction v2 を **毎日・安全・再現可能** に運用するための
「運用ルール」「実行手順」「復旧手段」をまとめた公式ドキュメントです。

設計方針は以下の通り：

- **安定核は触らない**
- **欠損・ズレは後段で補正する**
- **GUI は SST（Single Source of Truth）read-only**
- **壊れても“直し方が決まっている”状態を作る**

---

## 全体構成（役割分離）

```

run_daily.ps1        ← 安定核（生成）
run_daily_guard.ps1  ← 保険（整合・欠損補完）

┌──────────────┐
│   raw data   │  data/world_politics/YYYY-MM-DD.json
└──────┬───────┘
│
▼
┌──────────────┐
│   analysis   │  daily_news / sentiment / summary / diff
└──────┬───────┘
│
▼
┌──────────────┐
│    digest    │  view_model (dated / latest)
└──────┬───────┘
│
▼
┌──────────────┐
│     GUI      │  SST read-only
└──────────────┘

````

---

## 毎日の運用（必須）

### 実行コマンド（この順番）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_daily.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_daily_guard.ps1
````

### 役割

#### run_daily.ps1

* Fetcher / Analyzer / Digest / Sentiment を生成
* 「完走すること」を最優先
* 原則として **編集しない安定版**

#### run_daily_guard.ps1

* 当日分の不足成果物を補完
* `latest` と `dated` の整合を保証
* GUI が「止まらない」ための保険

---

## 重要な運用ルール

### 1. 欠損日を作らない（最重要）

以下の欠損は **後から復旧できない** 可能性が高い：

* `data/world_politics/YYYY-MM-DD.json`（raw）
* `data/world_politics/analysis/daily_news_YYYY-MM-DD.json`

**run_daily が失敗した日は、その日のうちに再実行すること。**

---

### 2. GUI は壊れていない可能性を疑う

GUI 表示が止まった場合でも：

* 多くは **データ欠損**
* または `latest` の不整合

GUI を直す前に、**必ず guard / report を確認**する。

---

## 補助スクリプト（公式ツール）

### ① 欠損チェック

```powershell
powershell -ExecutionPolicy Bypass -File scripts/report_sentiment_gaps.ps1 -Days 30
```

用途：

* raw missing / sentiment missing の可視化
* グラフが途切れる原因特定

---

### ② GUI 成果物の backfill（過去分）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/backfill_gui_artifacts.ps1
```

用途：

* `daily_news_YYYY-MM-DD.json` 等の補完
* GUI 表示の回復

---

### ③ sentiment 欠損の backfill

```powershell
powershell -ExecutionPolicy Bypass -File scripts/backfill_missing_sentiment.ps1 -Days 60
```

用途：

* raw が存在する日の sentiment 再生成
* グラフの復旧

※ raw / daily_news が存在しない日は生成不可（仕様）

---

### ④ latest の再同期

```powershell
powershell -ExecutionPolicy Bypass -File scripts/refresh_latest_artifacts.ps1
```

用途：

* GUI が古い日付で止まった場合の即効薬

---

## よくあるトラブルと対処

### Q. グラフが途中で止まる

→ `report_sentiment_gaps.ps1` を実行
→ 欠損日が存在する場合、それは **仕様上の欠損**

### Q. 今日の sentiment が表示されない

→ `run_daily_guard.ps1` を再実行
→ それでもダメなら `refresh_latest_artifacts.ps1`

### Q. Analyzer が JSON エラーで落ちる

→ raw JSON が壊れている可能性
→ `repair_daily_news_json.py`（guard / backfill 内で自動実行）

---

## Git 運用ルール（簡易）

* run_daily.ps1 / guard / ops scripts は **main に固定**
* GUI 調整中のファイルは混ぜない
* フェーズごとに commit を分ける

---

## 最終目標

* 毎日 2 コマンドで安定運用
* 欠損しても「直し方が決まっている」
* deploy しても怖くない状態

---

この Runbook は **運用経験に基づいて随時更新してよい**。
ただし「安定核を触らない」という原則だけは維持すること。

```

---

これで  
**「どこからどこまで？」問題は完全に解消**です。

このまま保存してください。  
（今は commit しなくてOK。GUI作業が落ち着いたらで大丈夫です）
```
