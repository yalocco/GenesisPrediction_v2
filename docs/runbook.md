# Runbook — GenesisPrediction v2

（2026-02-07 更新：run_daily + run_daily_guard を正式採用 / SST整合保証を追加）

---

## 0. 目的と位置づけ

GenesisPrediction v2 は、**未来を決めるシステムではない**。  
本 Runbook は、

- 迷わず運用できること
- 壊さず深められること
- 疲れている日でも判断を誤らないこと

を目的とした **最優先の運用台本**である。

> 本 Runbook は、チャット・一時的な判断・思いつきよりも優先される。

---

## 1. 基本思想（凍結）

- 観測 → 仮説 → 判断 の順を崩さない
- 数値は結論ではない
- アナログは示唆であり証拠ではない
- 判断は常に人間が行う
- 当日速報は扱わない（前日確定主義）
- STOP は最後の手段

---

## 2. 全体構成（役割分離）

- **自動処理**：材料を出す（events / anchors / analogs / daily_news / sentiment / daily_summary）
- **GUI**：読む・気づく・忘れないための窓（SST read-only）
- **人間**：1行で確定する（reflection）
- **docs (.md)**：判断と気づきを未来に残す

---

## 3. 日次正式ルーチン（SST保証 / GUI前提）

### 3.1 サーバ起動（必要なとき）

```powershell
cd D:\AI\Projects\GenesisPrediction_v2
.\.venv\Scripts\python.exe -m uvicorn app.server:app --host 127.0.0.1 --port 8000
