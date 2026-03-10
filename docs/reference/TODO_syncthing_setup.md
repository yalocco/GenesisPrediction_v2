# Syncthing 導入 TODO（明日）

## 前提
- data/ は Git 管理しない
- 同期は Syncthing
- 正データは自宅PC（Send Only）

---

## 手順

### 1. 自宅PC（メイン）
- [ ] Syncthing インストール
- [ ] http://127.0.0.1:8384 にアクセス
- [ ] data/ フォルダ追加
  - Folder Type: Send Only
  - File Versioning: Simple (Keep 3)

---

### 2. 会社PC（サブ）
- [ ] Syncthing インストール
- [ ] 自宅PCをデバイス追加
- [ ] data/ フォルダ追加
  - Folder Type: Receive Only

---

### 3. 確認
- [ ] ファイル数一致
- [ ] 容量一致
- [ ] Receive Only 側に Local Changes がない

---

## トラブル時
- 迷ったら 会社PC の data/ を削除して再同期
