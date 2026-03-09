# Contracts README  
GenesisPrediction v2 / Contracts Index

## 目的

本ディレクトリ（`docs/contracts/`）は、  
GenesisPrediction v2 における **内部・外部インターフェースの契約（Contract）** を集約する場所である。

ここに置かれる文書は、

- 実装（Analyzer / Digest / GUI）
- API
- 保存形式
- ViewModel

の **境界と責務を固定する正本**として扱われる。

---

## 位置づけ（法体系内）

本プロジェクトの docs は、以下の階層で整理される。

1. **constitution/**  
   - 最上位ルール（運用契約・禁止事項）
2. **specs/**  
   - 計算・生成物・解釈ルールの仕様
3. **contracts/**（本ディレクトリ）  
   - **コンポーネント間の約束事（契約）**
4. **runbook/**  
   - 日次運用・実行手順

contracts は、  
**「どう計算するか」ではなく  
「何を渡し、何を受け取るか」**を定義する。

---

## contracts に置くもの

以下の種類の文書を、このディレクトリに集約する。

- API 契約（例：Digest API）
- ViewModel 定義
- 保存・参照規約（Storage Convention）
- GUI / API 間の表示契約
- 将来の外部連携契約（あれば）

これらはすべて：

- **実装より優先**
- **口頭説明より優先**
- **チャットの提案より優先**

される。

---

## 想定される契約ファイル（例）

以下は、contracts 配下に置かれることを想定した代表例である。

- `digest_api_contract_v1.md`  
  - Digest ViewModel を提供する API の契約
- `digest_viewmodel_v1.md`  
  - Analyzer / Digest / GUI 間の表示契約
- `digest_view_storage_convention_v1.md`  
  - ViewModel / 画像などの保存・参照規約

※ 実体の有無に関わらず、  
**契約は必ずここに集約する方針**とする。

---

## 参照ルール（重要）

- 実装者・GUI・API は、  
  **contracts に定義された契約を前提として動作する**
- 契約に反する挙動は **不具合**として扱う
- 契約の抜け・未定義がある場合は、  
  実装で補うのではなく **契約を先に定義する**

---

## 変更ルール

- 契約文書の変更は **新バージョン作成のみ**許可する
- 既存契約の暗黙変更は禁止する
- 変更時は：
  - 変更理由
  - 影響範囲（Analyzer / Digest / GUI 等）
  を明記する

---

## 将来拡張

- sentiment 導入に伴う契約
- 複数 GUI / 外部サービス連携
- API v2 以降

これらはすべて、本ディレクトリ配下で追加・管理する。

---

## 結論

contracts は、

- 実装を縛るための場所ではなく
- **実装が迷わないための境界線**

である。

迷った場合は：
> **「それは仕様か？契約か？」**

と問い、  
境界の話であれば **contracts を正とする**。

---

（GenesisPrediction v2 / Contracts README v1）
