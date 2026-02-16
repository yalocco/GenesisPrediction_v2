# GenesisPrediction v2

GenesisPrediction v2 は、日次ニュース・各種データを取り込み、  
差分（diff）・観測ログ・可視化を通じて  
**「世界の変化を、驚かずに観測し続ける」**ためのシステムです。

本リポジトリでは、設計・運用の混乱（チャット跨ぎ / 口頭ルール / 部分修正）を避けるため、  
**docs/ を“正本（Single Source of Truth）”として運用**します。

---

## 🚀 Morning Ritual（正式エントリポイント）

GenesisPrediction v2 の日次処理は、**以下の1コマンドのみが正式手順**です。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_morning_ritual.ps1
```

### オプション

Guard付き実行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_morning_ritual.ps1 -Guard
```

日付指定実行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_morning_ritual.ps1 -Date 2026-02-16
```

### Morning Ritual が行うこと

- Analyzer 実行
- daily_news_latest 生成
- daily_news_YYYY-MM-DD.html 自動生成（自然治癒）
- FX Overlay 生成
- Health 期待名 fx_overlay_YYYY-MM-DD.png 自動生成（自然治癒）
- daily_summary_latest 正規化（自然治癒）
- FX rates 更新
- FX inputs 更新
- Data Health 生成

---

## 最優先（憲法 / Constitution）

本プロジェクトに関わる **すべての作業・設計相談・実装**は、  
以下の正本に従います。

- **docs/constitution/file_generation_rules_v1.md**

この文書で固定される重要事項（抜粋）：

- 修正・追加は **完全なコード全文 / 完全なファイル生成**のみ
- **差分提示・部分修正・手動編集は禁止**
- GUI は **正本（SST）を読むだけ**
  - 推測・再要約・HTML パース禁止
- 正本に反する挙動は **不具合／違反**

---

## 正本一覧（Docs Canon）

### 仕様 / Specs

- **FX 運用仕様（v1）**
  - `docs/specs/fx_operation_spec_v1.md`

- **Sentiment（感情スコア）仕様（v1）**
  - `docs/specs/sentiment_spec_v1.md`

> 「仕様」は、計算・生成物・解釈ルールを固定するための正本です。

---

## Daily Operation（従来手順）

GenesisPrediction v2 は、  
**生成（重い処理）** と **日付整合保証（軽い処理）** を分離して日次運用を行います。

### 従来の分割実行手順

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_guard.ps1
```

※ 正式運用は Morning Ritual を使用してください。

---

詳細な日次運用手順、障害時の対処、設計意図の全体像については  
`docs/runbook.md` を正本（SST）として参照してください。
