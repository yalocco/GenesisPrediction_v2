# GenesisPrediction v2

GenesisPrediction v2 は、日次ニュース・各種データを取り込み、
差分（diff）・観測ログ・可視化を通じて「世界の変化」を安定的に観測するためのシステムです。

本リポジトリでは、設計・運用の混乱（チャット跨ぎ / 口頭ルール / 部分修正）を避けるため、
**docs/ を“正本（Single Source of Truth）”として運用**します。

---

## 最優先（憲法 / Constitution）

本プロジェクトに関わる **すべての作業・設計相談・実装**は、
以下の正本に従います。

- **docs/constitution/file_generation_rules_v1.md**

この文書で固定される重要事項（抜粋）：
- 修正・追加は **完全なコード全文 / 完全なファイル生成**のみ
- **差分提示・部分修正・手動編集は禁止**
- GUI は **正本を読むだけ**（推測・再要約・HTMLパース禁止）
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

## 直下の使用ノート（作業者向け）

以下は「正本」ではなく、作業者がすぐ参照できるように置くノートです。
（必要に応じて将来 docs/notes に移設してもOK）

- `python.md`
- `github.md`

---

## チャット運用（重要）

新しいチャット／スレッドでは、冒頭で必ず以下を宣言します。

例：
> このチャットは、共有ファイル倉庫の  
> `docs/constitution/file_generation_rules_v1.md`  
> に従って運用する。

必要に応じて、適用する正本（仕様）を追加で宣言します。

例：
> 加えて、`docs/specs/sentiment_spec_v1.md` に従って Sentiment を進める。

---

## 方針

- docs/ が正本（契約・仕様・運用の核）
- コードは正本に従って生成し、再現可能性を最優先する
- 「未来を当てる」ではなく、世界の温度変化を定量化し、驚かないための観測装置として育てる

---

## Quick Start（最小）

1. Python venv を有効化
2. GUI 起動（例）

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.server:app --reload --host 127.0.0.1 --port 8000
