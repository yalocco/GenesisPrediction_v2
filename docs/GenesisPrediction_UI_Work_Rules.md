
# GenesisPrediction UI 作業ルール

## 目的
GenesisPrediction の UI 作業において

- スレッド破損
- ストリームエラー
- コピー貼り付け事故
- 差分混入

を防ぎ、安全に UI ファイルを修正するためのルール。

このルールは **GenesisPrediction v2 UI 開発の標準作業手順**とする。


---

# 1. 基本原則

GenesisPrediction UI は

- HTML
- CSS
- JavaScript

が **1000行級の単一ファイル**になることが多い。

そのため

**長文貼り付けは禁止**とする。


---

# 2. ファイル生成ルール

UIコード生成は以下の順番で行う。

① ダウンロードファイル生成（標準）

必ず最初に

.html  
.css  
.js  
.md  

の **ダウンロードファイル形式**で生成する。


② ダウンロード不可の場合

zip形式で生成する。


③ 最終手段

上記が両方失敗した場合のみ

**長文完全ファイル**を使用する。


---

# 3. 差分禁止ルール

GenesisPrediction UI では

差分パッチ  
部分修正  
行番号修正  

は禁止。

必ず

**完全ファイル（Full File）**

のみ生成する。


理由

UIファイルは

- インデント崩れ
- 括弧不一致
- CSS破損

が起きやすいため。


---

# 4. UIスレッド運用ルール

UI作業スレッドでは

禁止

- 長文HTML貼り付け
- 長文CSS貼り付け
- 長文JS貼り付け

許可

- ダウンロード生成
- zip生成
- 短い説明


---

# 5. UIファイルサイズ基準

以下を基準とする

0〜200行 → 通常生成可  
200〜500行 → ダウンロード推奨  
500行以上 → 必ずダウンロード生成

---

# 6. UI構造統一ルール

GenesisPrediction UI は以下の構造を統一する。

ページ構造

Header  
Global Status  
Hero  
Cards  
Timeline  
Footer


---

# 7. Prediction系UI統一

以下のページはデザイン統一対象

prediction.html  
prediction_history.html  
digest.html  
sentiment.html  
overlay.html  

統一対象

- Header
- Card構造
- Status表示
- Color theme
- Fontサイズ


---

# 8. UI作業フロー

UI作業は以下の手順で行う

① UI修正スレ作成  
② 対象HTML確認  
③ ダウンロード生成  
④ VSCode上書き  
⑤ ローカル確認  
⑥ git commit  
⑦ git push  


---

# 9. Gitルール

UI変更時

git add  
git commit  
git push  

commit例

UI: prediction history layout fix


---

# 10. スレッド保護ルール

UIスレは

**重くなったら即終了**

新スレを作る。

理由

ChatGPTは

- 長文
- HTML
- CSS

が増えると

**ストリームエラーが発生するため。**


---

# 11. 推奨スレタイトル

UI作業スレは以下の形式にする

GenesisPrediction UI 修正  
（対象ファイル名）

例

GenesisPrediction UI 修正  
(prediction_history.html)


---

# 12. 最重要ルール

UI修正は

**必ずダウンロード生成で行う。**

長文貼り付けは禁止。


---

# End
