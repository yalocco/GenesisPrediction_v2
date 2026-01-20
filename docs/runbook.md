# Runbook — GenesisPrediction v2

（2026-01-20 更新：GUI運用と 1-line reflection を正式採用）

---

## 0. 目的と位置づけ

GenesisPrediction v2 は、**未来を決めるシステムではない**。
本 Runbook は、

* 迷わず運用できること
* 壊さず深められること
* 疲れている日でも判断を誤らないこと

を目的とした **最優先の運用台本**である。

> 本 Runbook は、チャット・一時的な判断・思いつきよりも優先される。

---

## 1. 基本思想（凍結）

* 観測 → 仮説 → 判断 の順を崩さない
* 数値は結論ではない
* アナログは示唆であり証拠ではない
* 判断は常に人間が行う
* 当日速報は扱わない（前日確定主義）
* STOP は最後の手段

---

## 2. 全体構成（役割分離）

* **自動処理**：材料を出す（events / anchors / analogs）
* **GUI**：読む・気づく・忘れないための窓
* **人間**：1行で確定する
* **docs (.md)**：判断と気づきを未来に残す

---

## 3. 日次正式ルーチン（GUI前提）

### 3.1 サーバ起動（必要なとき）

```powershell
cd D:\AI\Projects\GenesisPrediction_v2
.\.venv\Scripts\python.exe -m uvicorn app.server:app --host 127.0.0.1 --port 8000
```

---

### 3.2 GUIを開く

* [http://127.0.0.1:8000](http://127.0.0.1:8000)
* 表示日付を確認（latest / 指定日）

---

### 3.3 Analyzer 実行

* Step 1: Run Analyzer
* 前日分の daily_summary_YYYY-MM-DD.json を生成

---

### 3.4 HTML Digest

* Step 2: Build HTML Digest
* 日次ニュースの俯瞰用（判断材料）

---

### 3.5 可視化（任意）

* Step 3: Plot
* regime / confidence 系グラフ

---

### 3.6 Observation Log

* Step 4: Observation Log
* observation_YYYY-MM-DD.md / json を生成

---

### 3.7 1-line Reflection（重要）

* GUI 起動時、所感が未記入の日は **ダイアログが表示される**
* 1行だけ所感を書く、または「今日は書かない」を選ぶ
* 所感は自動生成しない

保存先：

* docs/observation.md

役割：

* 当たり外れを書かない
* 見え方の変化・次に観測すべき点を書く

---

## 4. observation.md の運用ルール

* 自動生成はヒントまで
* 人間の所感は 1行で十分
* 書かない日があっても異常ではない
* 後から読んで意味が分かることを優先

---

## 5. 禁止事項（事故防止）

* 数値だけで判断しない
* confidence を手動で盛らない
* 1日に複数の結論を確定しない
* .md を自動文で埋めない

---

## 6. トラブル時の原則

* 生成物が無い → 前日データを確認
* events が無い → SKIP は正常
* 迷ったら observation.md の最後を見る

---

## 7. 状態宣言

GenesisPrediction v2 は、
**壊さずに深めるフェーズ**に入っている。

急がず、1日1行で十分。
