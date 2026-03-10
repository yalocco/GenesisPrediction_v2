# GUI安定化フェーズ2（ダウンロード徹底運用）運用ルール

本書は GenesisPrediction v2 の GUI を **sentiment baseline** に統一し、以後のUI編集における **人間ミスをゼロに近づける**ための運用ルール（SST）です。

- 凍結タグ（Freeze Point）: `gui-ui-stable-v2.0`
- 運用対象: `app/static/*.html`（特に `index.html / sentiment.html / overlay.html`）
- ゴール: **UIの統一感・再現性・安全性（コピペ事故ゼロ）**

---

## 0. 大原則（絶対）

### A. GUIファイルは「ダウンロード運用」のみ
- **200行超の貼り付け禁止**
- GUI関連の受け渡しは **必ずファイル添付（ダウンロード）**で行う
- 例外は作らない（例外が事故の起点になる）

### B. 差分（パッチ）禁止
- 出力は **完全ファイル全文のみ**
- 「差分追加」「部分修正」「パッチ方式」の提案は禁止

### C. 1ターン = 1作業
- 1回の作業で触る対象を1つに絞る
- 複数ファイル編集は原則しない（必要なら作業を分割して複数ターンにする）

---

## 1. SST（Single Source of Truth）と参照ルール

### 1.1 UI基準（Baseline）
- **sentiment.html を基準（baseline）**とし、以下の要素を統一する
  - 背景（radial + linear）
  - topbar の構造（ブランド + nav pills）
  - body幅（container max-width）
  - 見出し/本文フォントサイズ
  - ガラスカード（glass / stroke / shadow）

### 1.2 静的配信・参照
- 実行環境は `server: static/analysis mount` が正常であること
- JSON は `analysis/*_latest.json` を優先参照（存在しない場合は fallback を使う）

---

## 2. 作業フロー（推奨・安全手順）

### 2.1 ブランチ運用（推奨）
- UI作業は原則 `main` 直ではなく、短命ブランチを推奨
  - 例: `wip/gui-phase2-YYYYMMDD`
- ただし「軽微な1ファイル整形」でも **差分を小さく**保つ

### 2.2 作業単位（チェックリスト）
1. 対象ファイルを決める（例: `app/static/index.html`）
2. ダウンロードで受け取る（貼り付けしない）
3. ローカルで上書き
4. ブラウザ **Ctrl+F5** で確認
5. `git diff` を確認（想定外の変更がないこと）
6. `git status` が意図通りか確認
7. commit → push（必要ならtag）

---

## 3. UI凍結（Freeze）運用

### 3.1 凍結の意味
- 「この状態に戻せば必ず動く」という復旧点
- UI改善はこの凍結点からのみ前進させる

### 3.2 凍結タグの付け方
- 安定点でのみ tag を打つ（未検証状態にタグは禁止）
- 例:
  - `git tag gui-ui-stable-v2.0`
  - `git push --tags`

### 3.3 凍結点からの復旧手順
- UIが崩れたら、まず凍結点へ戻して再確認
  - `git checkout gui-ui-stable-v2.0 -- app/static/index.html`
  - `git checkout gui-ui-stable-v2.0 -- app/static/sentiment.html`
  - `git checkout gui-ui-stable-v2.0 -- app/static/overlay.html`

---

## 4. 「不要JSON生表示」ポリシー

### 4.1 原則
- 通常表示では **生JSONを画面に出さない**
- デバッグ用途は `details`（折りたたみ）へ隔離する

### 4.2 例外（デバッグ導線）
- 「Open JSON」ボタン等で、別タブでJSONを開けるようにする
- `raw (debug)` はデフォで閉じる

---

## 5. フェーズ2の作業範囲（スコープ）

### 5.1 やること（候補）
- Data Health 表示整形
- Daily Summary 表示整形
- 不要JSON生表示の整理
- GUI構造の凍結タグ運用の確立（本書）

### 5.2 やらないこと（フェーズ2では凍結）
- 大規模UI刷新（レイアウト全面変更）
- ブランド変更
- CSSフレームワーク導入
- 別ページの大改造（必要なら別フェーズ/別スレ）

---

## 6. 完了条件（フェーズ2）

- 主要ページ（Home/Overlay/Sentiment）のヘッダー・背景・幅が統一
- 日次運用で「見た目が崩れない」こと
- 人間ミスの起点（貼り付け/差分/複数作業）を排除
- 凍結タグに戻せば必ず復旧できる

---

## 付録: 代表コマンド集

```powershell
# 変更確認
git status
git diff

# 反映
git add -A
git commit -m "GUI: <one small change>"
git push

# 安定点タグ
git tag gui-ui-stable-v2.0
git push --tags
```
