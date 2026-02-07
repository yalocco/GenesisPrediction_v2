# GenesisPrediction v2｜GUI 商用品質チェックリスト（SST前提）

目的：GUI は **SST（read-only）を絶対に崩さず**、表示だけを商用品質に保つ。

---

## 0) 重要原則（破ったら戻す）
- GUI は **再計算しない**（analysis/ 以下の JSON/PNG/CSV を読むだけ）
- GUI は **書き戻さない**（API POST / PUT / ファイル生成禁止）
- パスは原則 **絶対参照**（`/static/...` / `/analysis/...`）
- CSS は原則 **`/static/app.css` を正**（bridge で事故を増やさない）

---

## 1) ページ別・最低合格条件

### Home（index.html）
- [ ] `/static/app.css` が読み込まれている
- [ ] KPI は 4桁表示（表示のみ丸め、ロジック不変）
- [ ] 404/欠損があっても白ページ化しない
- [ ] ナビ（Home/Overlay/Sentiment/Digest）が全ページで同一

### Sentiment（sentiment.html）
- [ ] `/static/app.css` 直リンク
- [ ] `sentiment_latest.json` が読めない場合でもクラッシュ理由が表示される
- [ ] `daily_news_latest.json` が無い場合でも **WARN 表示で継続**
- [ ] KPI は 4桁、テーブルは 6桁（分析向け）
- [ ] 画像無しでも行が崩れない（NO IMAGE のプレースホルダ）
- [ ] 検索／sourceフィルタ／sort が動く
- [ ] URL正規化による重複排除が働く（GUI側のみ）

### Overlay（overlay.html）
- [ ] `/static/app.css` 直リンク
- [ ] 画像やチャートが無くてもページ自体は表示される
- [ ] “生成物が無い” は NG ではなく「not available / WARN」の扱いにする（可能な範囲で）

### Digest（digest.html）
- [ ] `/static/app.css` 直リンク
- [ ] 赤枠（JS例外）が出ない
- [ ] `daily_summary_latest.json` が無い場合に理由が表示される
- [ ] Raw JSON の折りたたみが動く

---

## 2) 見た目（商用チェック）
- [ ] 70〜90% 縮小でも破綻しない（主要情報が読める）
- [ ] 余白（カード内padding / カード間spacing）が統一
- [ ] ボタン／バッジ／ピルの形・高さが統一
- [ ] テーブルの sticky header が崩れない
- [ ] モバイル幅で過剰な列を隠す（最低限の可読性）

---

## 3) 変更時のルール（事故防止）
- [ ] 変更は **1ファイルずつ**（貼る→生成→上書き→ブラウザ確認）
- [ ] “styles.css 経由” を増やさない（再発源）
- [ ] JS 修正は「壊れない」「理由が出る」を優先（サイレント失敗禁止）
- [ ] 可能なら `Ctrl+F5` でキャッシュ影響を排除して確認

---

## 4) 最終確認（deploy前）
- [ ] 4ページすべてを開いて、console error が出ない
- [ ] 生成物（analysis/）が欠損している日でも、白ページにならない
- [ ] “SST（read-only）” 表記が全ページにあり、挙動も一致している
