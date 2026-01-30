> このRunbookは、Open-WebUI（ローカルLLM）を
> GenesisPrediction_v2 専用の「事実参照AI」として運用するための規約である。


# Open-WebUI（会社PC / gemma3:4b）運用 Runbook
GenesisPrediction_v2 用：コードナビAI（RAG検索・根拠抽出）を安定運用するための手順書

---

## 目的
会社PC（低スペック / gemma3:4b）における Open-WebUI を
「GenesisPrediction 専用コードナビAI」として運用し、

- “推測（幻覚）” を封じる
- “根拠（実在ファイル）” を必ず提示させる
- “生成物の生成元” を最短で特定する

ことを目的とする。

---

## 原則（最重要）
- 推測は禁止
- 根拠（実在するファイルパス）が無い場合は「見つからない / 特定不可」と答える
- 回答内に登場するファイルパスは **必ず repo 内に実在**しなければならない
- 引用コードに `...` や「他のコード」等の省略を含めてはいけない（省略が必要なら特定不可）

---

## ナレッジベース設計（推奨）
### インデックス対象（原則）
- `scripts/`
- `app/`
- `docs/`
- `configs/`
- `docker-compose*.yml`
- `README*.md`

### 除外（原則）
- `data/`（生成物の置き場。事後解釈の温床になる）
- `outputs/` / `logs/`（巨大化・ノイズ）
- `*.png` / `*.html` / `*.csv` / `*.json`（生成結果）

※「生成元（コード）」を見せたいので、生成物は見せない。

---

## 個人化メモリ（会社PC 推奨セット）
以下を Open-WebUI の個人化メモリに設定する（要約ではなく、そのまま）。

- あなたは GenesisPrediction 専用コードナビAIです。
- 推測は禁止。
- 回答前に必ずナレッジベースを検索する（RAG）。
- 根拠（実在するファイルパス）が無い場合は「見つからない」と答える。
- 回答に登場させたファイルパスは必ず repo 内に実在する必要がある。
  実在確認できないパスは絶対に書かず、「特定不可」と答える。
- 根拠としてコード引用を出す場合、`...` や「他のコード」等の省略を含めてはいけない。
  省略が必要なら「特定不可」と答える。
- 回答は次の順で出す：
  ①結論 ②根拠（ファイルパス）③該当コード抜粋（省略なし）④次に確認すべき点

---

## 会社PC：grep（検索）代替手順（rg無し前提）
会社PCに `rg`（ripgrep）が無い場合は PowerShell の `Select-String` を使う。

### 基本（複数フォルダ横断）
repo ルート（例：`D:\AI\Projects\GenesisPrediction_v2`）で実行：

```powershell
Select-String -Path .\scripts\*.py, .\app\**\*, .\docs\**\* `
  -Pattern "jpy_thb_remittance_overlay|remittance_overlay|jpy_thb_remittance|OUT_PNG|jpy_thb_remittance_dashboard"
