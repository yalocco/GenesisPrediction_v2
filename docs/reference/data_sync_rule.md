# Data Sync Rule（Syncthing）

## Scope
- GenesisPrediction_v2/data/ の同期ルールを定義する
- 個人利用のみ
- 商用利用は別途設計する

## Policy
- data/ は Git 管理しない
- 同期は Syncthing を使用
- 正データは 1 台のみとする

## Tool
- Syncthing

## Folder Structure
- 対象フォルダ: GenesisPrediction_v2/data/
- data/ は Git 管理しない

---

## Syncthing Configuration
- 同期ツール: Syncthing
- File Versioning: Simple File Versioning (Keep 3)

---

## Send Only / Receive Only Design

### Main PC（自宅PC）
- Folder Type: Send Only
- data/ の編集はこの PC のみ

### Sub PC（会社PC / ノート）
- Folder Type: Receive Only
- data/ は参照専用

---

## Ignore Rules (.stignore)
以下は data/.stignore に記載する。

- OS / Editor 一時ファイル
- Python キャッシュ
- 一時作業ファイル
- cache/ / tmp/

---

## Accident Prevention Rules
- 双方向同期は禁止
- Receive Only 側で編集しない
- data/ を Git に add しない
- 迷ったら Receive Only 側を削除して再同期

---

## Initial Sync Procedure
1. Main PC に Syncthing をインストール
2. data/ を Send Only で追加
3. Sub PC に Syncthing をインストール
4. Receive Only で接続
5. 初回同期を確認

---

## Reset Procedure
### Receive Only 側を初期化する場合
1. Syncthing 停止
2. ローカル data/ を削除
3. Syncthing 起動
4. 再同期
