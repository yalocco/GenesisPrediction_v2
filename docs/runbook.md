# Runbook — GenesisPrediction v2

（2026-02-16 更新：Morning Ritual 正式採用 / 差分追加禁止固定）

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
- Data Health は監査装置であり、自然に OK へ収束する設計とする

---

## 2. 全体構成（役割分離）

- **自動処理**：材料を出す（events / anchors / analogs / daily_news / sentiment / daily_summary / fx_overlay）
- **GUI**：読む・気づく・忘れないための窓（SST read-only）
- **人間**：1行で確定する（reflection）
- **docs (.md)**：判断と気づきを未来に残す

---

## 3. 日次正式ルーチン（唯一の入口）

### 3.1 Morning Ritual（正式）

毎朝はこれだけ実行する：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
```

Guard付き：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Guard
```

日付指定（検証・復旧）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-16
```

---

### 3.2 Morning Ritual が保証するもの

- Analyzer 実行
- daily_news_latest 生成
- daily_news_YYYY-MM-DD.html 自動生成
- FX Overlay 生成
- fx_overlay_YYYY-MM-DD.png Health alias 自動生成
- daily_summary_latest 正規化
- FX rates / inputs 更新
- Data Health 生成

> 個別スクリプト単体実行は原則禁止。

---

## 4. GUI運用原則（SST固定）

- GUI は正本を読むのみ
- HTMLを解析して推測しない
- JSONを再構築しない
- SST外の推論禁止

---

## 5. Data Health 方針

- WARN は設計修正で消す
- 手動コピーで消さない
- missing を直すのではなく「生成構造」に組み込む
- OK=10 / WARN=0 / NG=0 を基準とする

---

## 6. 変更ルール（凍結）

- 差分追加（部分修正・パッチ方式）禁止
- 必ず完全ファイル全文で提示
- 変更は 1ターン=1作業
- git diff 確認 → commit → push
- 壊れたら即 restore

---

## 7. 人間の役割

- 数値を信じすぎない
- 過去の判断と照合する
- reflection を1行で残す
- 迷ったら止まる

---

## 8. 最終原則

GenesisPrediction は予言装置ではない。  
これは「冷静さを保つための観測装置」である。
