# Decision Log

このファイルは「何を・なぜ・どう決めたか」を記録する。
AIはこの情報を優先参照し、一貫した判断を行うこと。

---

## Entry Template

Date: YYYY-MM-DD
Topic:
Decision:
Reason:
Impact:

---

## Entries

### Entry 001
Date: 2026-03-20
Topic: Open WebUI モデル選定
Decision: ministral-3:14b をメインに採用
Reason:
- 日本語安定性が高い
- RAGとの相性が良い
- 出力の一貫性がある
Impact:
- 設計・思考は ministral-3 を使用
- コード生成は別モデル併用

---

### Entry 002
Date: 2026-03-20
Topic: AIの役割定義
Decision: AIを「相棒」として扱う
Reason:
- 長期的なプロジェクトに必要
- 一貫した思考支援が可能になる
Impact:
- 全ての応答は協働前提
- 単発ツール的な応答は禁止