# GenesisPrediction UI Work Rules

GenesisPrediction の UI 作業では  
HTML / CSS / JS が大型化しやすく、  
ChatGPT のストリームエラーやコピー事故が発生しやすい。

そのため UI 作業では  
**ファイル受け渡し方法の優先順位を固定する。**

このルールは  
GenesisPrediction UI 作業スレで常に適用する。

---

# UI File Delivery Protocol
（UIファイル受け渡しルール）

UIファイル生成時は  
以下の優先順位で提示する。

```

① ダウンロード
② ZIP
③ 本文
④ Canvas（最終手段）

```

この順序は **必ず守る。**

---

# ① Download（最優先）

通常は **ダウンロードリンク方式**を使用する。

理由

- 長文 HTML でも安全
- コピー事故を防げる
- スレッド消費を防ぐ
- UI作業の速度が最も安定する

対象ファイル例

```

prediction.html
sentiment.html
digest.html
overlay.html
prediction_history.html

```

UI修正では  
**原則 Download を使用する。**

---

# ② ZIP

ダウンロードリンクが反応しない場合は  
**ZIPでまとめて提供する。**

対象例

```

prediction_ui_package.zip
ui_fix_package.zip
ui_patch_package.zip

```

ZIPはブラウザのダウンロード失敗に強いため  
Download が使えない場合の **第2選択肢とする。**

---

# ③ 本文

Download / ZIP が使用できない場合のみ  
**本文で提示する。**

注意

- HTML / CSS は非常に長くなる
- スレッドが急速に消費される
- コピー事故が起きやすい

そのため **通常は推奨しない。**

---

# ④ Canvas（最終手段）

Canvas は以下の理由で  
**最終手段とする。**

問題点

- 生成速度が遅い
- ストリームエラーが起きやすい
- UI作業では試行回数が多く効率が悪い
- 途中保存が不安定な場合がある

そのため

```

Download → ZIP → 本文 → Canvas

```

の順序を厳守する。

---

# UI Work Principle

UI作業では以下のサイクルが何度も発生する。

```

生成 → 確認 → 修正 → 再生成

```

この作業を高速に回すため  
**最も安全で高速なファイル受け渡し方法を優先する。**

---

# Purpose

このルールの目的

- UI作業の速度を落とさない
- スレッド消費を抑える
- コピー事故を防ぐ
- UI修正サイクルを高速化する
- AI / 人間の作業効率を維持する

---

GenesisPrediction UI作業では  
このプロトコルを **標準ルールとして使用する。**
```

---

# この `.md` はとても良いです

理由はシンプルで、あなたのプロジェクトでは

* HTML 800〜1500行
* CSS 600〜1000行
* JS 500〜900行

普通に出るので、

**このルールがないと毎回スレが壊れます。**

これは **GenesisPrediction専用の重要運用ルール**です。

---

もしよければですが、
UI系 `.md` に **あと1つだけ入れるとさらに強くなります。**

それは

**UI Layout Standard**

```
Header
Global Status
Hero
Main Panels
Cards
Footer
```
