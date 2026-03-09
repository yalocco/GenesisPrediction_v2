# UI System (GenesisPrediction v2)

Version: 2.0 Status: Active Purpose: GenesisPrediction v2 の UI
構造・責務・共通レイアウト・ページ役割を固定する Last Updated:
2026-03-08

------------------------------------------------------------------------

# 0. Purpose

このドキュメントは、GenesisPrediction v2 の UI システム全体を定義する。

目的

-   新しいAIが UI 構造を誤解しないようにする
-   各ページの責務を固定する
-   共通レイアウトの構造を明文化する
-   UI と scripts / data / analysis の責務分離を維持する
-   Prediction / Prediction History を含む現行UI構造を正として記録する

------------------------------------------------------------------------

# 1. UI の最重要原則

GenesisPrediction の UI は

``` text
表示レイヤ
```

である。

最重要ルール

``` text
UI は data / analysis を読むだけ
UI は再計算しない
UI は分析ロジックを持たない
```

つまり

``` text
scripts → data / analysis を生成
UI → それを表示する
```

GenesisPrediction 全体の原則では

``` text
analysis = Single Source of Truth
```

である。

ただし現行UIでは、ページにより以下を読む。

``` text
data/world_politics/analysis/
data/digest/
data/fx/
analysis/prediction/
analysis/prediction/history/
```

この読み分けは runtime の現行配置に基づく表示依存であり、 UI
が真実を上書きすることを意味しない。

------------------------------------------------------------------------

# 2. UI の役割

UI の役割は次の4つに限定する。

## 2.1 表示

JSON / CSV / PNG / history を整形して見せる。

## 2.2 ナビゲーション

ページ間移動を統一する。

## 2.3 fallback

データ欠損時に落ちずに表示を継続する。

## 2.4 比較可視化

Prediction History のように、 既存 snapshot 同士の比較表示を行う。

重要:

``` text
比較表示 = UI の責務
予測生成 = UI の責務ではない
```

------------------------------------------------------------------------

# 3. UI 配置

UI の主要配置は以下。

``` text
app/static/
├─ index.html
├─ overlay.html
├─ sentiment.html
├─ digest.html
├─ prediction.html
├─ prediction_history.html
├─ app.css
└─ common/
   ├─ header.html
   ├─ footer.html
   └─ layout.js
```

------------------------------------------------------------------------

# 4. 現行ページ一覧

GenesisPrediction v2 の現行主要ページは以下。

``` text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

標準ナビゲーションもこの順序を基本とする。

------------------------------------------------------------------------

# 5. UI 共通レイアウト

現行 UI は、共通 header / footer / layout.js を使う構造を採用する。

共通骨格

``` text
#site-header
.container
page content
#site-footer
/static/common/layout.js
```

役割

## header.html

-   ブランド表示
-   共通ナビゲーション
-   ページ横断の入口統一

## footer.html

-   フッター表示
-   ブランド / コピーライト / 補助導線
-   ページ末尾構造の統一

## layout.js

-   header / footer を各ページへ差し込む
-   アクティブページ判定
-   共通レイアウトの読み込み
-   ページ間の統一感を維持する

重要原則

``` text
共通レイアウトは表示構造の共通化であり、
分析ロジックの共通化ではない
```

------------------------------------------------------------------------

# 6. app.css の責務

共通スタイルは

``` text
app/static/app.css
```

に置く。

役割

-   共通 topbar
-   nav pill
-   container 幅
-   card / glass / stroke / shadow
-   common typography
-   共通 spacing
-   共通 KPI / panel / grid の見た目

原則

``` text
共通にすべき見た目は app.css
ページ専用の微調整だけ各HTML内 style
```

大きなUI統一変更は、まず app.css を確認する。

------------------------------------------------------------------------

# 7. 各ページの責務

## 7.1 Home (index.html)

Home はプロジェクトの入口ページである。

役割

-   全体状況の軽量サマリー
-   各ページへの導線
-   最新状態の概要確認

表示対象の例

-   Summary
-   Data Health
-   Sentiment snapshot
-   Events / Highlights
-   Prediction 導線

Home は

``` text
詳しい分析をしない
```

ことが重要である。

詳しい内容は各専門ページへ委譲する。

------------------------------------------------------------------------

## 7.2 Overlay (overlay.html)

Overlay は FX 判断と可視化のページである。

役割

-   pair ごとの overlay image を表示する
-   decision JSON を表示する
-   remittance / FX monitoring の判断表示を行う

表示対象

-   JPYTHB
-   USDJPY
-   USDTHB
-   MULTI

Overlay は pair selector に応じて 複数候補を順に探索し、
取得できた最初の画像 / JSON を使う。

重要

``` text
Overlay の fallback は表示継続のため
正式成果物の命名規則そのものではない
```

命名や生成責務は scripts 側にある。

------------------------------------------------------------------------

## 7.3 Sentiment (sentiment.html)

Sentiment はニュース感情分析の表示ページである。

役割

-   per-article sentiment を見せる
-   KPI を見せる
-   trend / timeseries を見せる
-   thumbnail / source / sentiment label を表示する

主な分類

``` text
positive
negative
neutral
mixed
unknown
```

ただし unknown は暫定・欠損・旧schema吸収時に起こり得るため、
大量発生時は UI より先に source JSON を確認する。

Sentiment は

``` text
表示ページ
```

であり、label の決定を再実装しない。

------------------------------------------------------------------------

## 7.4 Digest (digest.html)

Digest は Daily Summary / Highlight UI である。

役割

-   summary を表示する
-   KPI を表示する
-   top highlights を表示する
-   article list を表示する
-   sort を切り替える

表示構造の基本

``` text
Summary
KPI
Highlights
Articles
```

重要

-   Digest の正式 source は view_model_latest.json
-   cards 件数と全 article 件数が一致しないことはあり得る
-   Highlights は抽出表示
-   Articles は記事一覧表示

Digest は、見た目を作るが、risk / score / sentiment を再計算しない。

------------------------------------------------------------------------

## 7.5 Prediction (prediction.html)

Prediction は runtime が生成した予測 snapshot の表示ページである。

役割

-   latest prediction の可視化
-   overall risk / dominant scenario / confidence 表示
-   watchpoints / drivers / invalidation / implications 表示
-   Global Status の共通表示

Prediction の本体は

``` text
prediction_latest.json
```

を正とする。

重要

``` text
Prediction UI は scenario を生成しない
Prediction UI は confidence を推定しない
Prediction UI は summary を捏造しない
```

------------------------------------------------------------------------

## 7.6 Prediction History (prediction_history.html)

Prediction History は時系列 review UI である。

役割

-   過去の prediction snapshot を読む
-   risk drift / confidence drift / scenario shift を見せる
-   latest 7 / latest 30 / all などの window 表示を行う
-   研究ログの閲覧を支援する

重要

``` text
Prediction History は history を読む
latest prediction を history の代用にしない
```

また、

``` text
比較表示 = 許可
再予測 = 不可
```

である。

------------------------------------------------------------------------

# 8. UI データの考え方

ページが読む source は異なるが、 原則は次の通り。

``` text
latest を優先
history は review 用
fallback は表示継続専用
```

つまり

-   Home = latest overview
-   Overlay = pair-specific latest + fallback
-   Sentiment = sentiment latest
-   Digest = digest view model latest
-   Prediction = prediction latest
-   Prediction History = prediction history

正式な依存関係は

``` text
docs/ui_data_dependencies.md
```

を正とする。

この文書は構造と責務を記録する。

------------------------------------------------------------------------

# 9. fallback の扱い

UI は落ちないことが重要であるため、 必要最小限の fallback を持ってよい。

ただし fallback には制限がある。

## 許可されるもの

-   画像が無い時の代替画像
-   JSON 欠損時の unavailable state
-   旧 field 名との後方互換吸収
-   Overlay の候補探索
-   Digest / Home の暫定 summary fallback

## 禁止されるもの

-   risk の再計算
-   sentiment の再分類
-   prediction の生成
-   scenario probability の捏造
-   履歴が無いのに history を作ったふりをする

原則

``` text
fallback は保険
source of truth の代用ではない
```

------------------------------------------------------------------------

# 10. Global Status / 共通表示

現行UIでは、Prediction / Prediction History を含め、 上部に共通的な
status 表示を置く場合がある。

この共通表示は

``` text
補助的な overview
```

であって、 各ページ本体の source of truth を置き換えない。

たとえば Prediction ページでは

-   Global Status = 補助表示
-   prediction_latest.json = 本体

である。

------------------------------------------------------------------------

# 11. UI と Layout Standard の関係

GenesisPrediction では、 見た目の統一とデータ依存は分離して管理する。

関係

``` text
ui_system.md
    = UI構造 / ページ責務 / 共通レイアウトの定義

ui_data_dependencies.md
    = 各ページがどのJSON / PNG / CSVを読むかの定義

ui_layout_standard.md
    = 見た目 / 配置 / 骨格 / 高さ合わせ等の標準
```

この3つを混ぜないことが重要である。

------------------------------------------------------------------------

# 12. UI 編集時の優先確認

UI を直す時は、次の順で確認する。

## Step 1

何のページを直すか

``` text
Home / Overlay / Sentiment / Digest / Prediction / Prediction History
```

## Step 2

そのページの source は何か

``` text
latest / history / png / csv / view model
```

## Step 3

問題はどこか

``` text
source 側か
UI 側か
共通 layout 側か
app.css 側か
```

## Step 4

必要な docs を更新する

-   UI構造変更 → ui_system.md
-   データ依存変更 → ui_data_dependencies.md
-   レイアウト標準変更 → ui_layout_standard.md

------------------------------------------------------------------------

# 13. UI 事故防止ルール

GenesisPrediction の UI は事故が起きやすい領域である。

そのため以下を守る。

``` text
1ターン = 1作業
差分提案禁止
完全ファイルのみ
長文HTMLはダウンロード方式優先
必要ならZIP
それでも不可なら長文表示
```

また、

``` text
長大ファイルをチャットで直接いじり続けない
```

ことが重要である。

------------------------------------------------------------------------

# 14. 典型的な判断ルール

## UI が崩れた

まず source を確認する。

-   data / analysis が正しいか
-   共通 layout の差し込みが壊れていないか
-   app.css で全体が崩れていないか

## 数値が出ない

UI より先に source JSON を確認する。

## Prediction が空

prediction_latest.json か history 側の不足を疑う。

## Overlay が出ない

pair-specific latest / fallback 候補 / ブラウザキャッシュを確認する。

重要原則

``` text
UIを疑う前に source を見る
```

------------------------------------------------------------------------

# 15. GenesisPrediction における UI 思想

GenesisPrediction の UI は 派手さのためではなく、

``` text
理解しやすく
壊れにくく
比較しやすく
毎日見られる
```

ために存在する。

UI は

``` text
判断支援の窓
```

である。

したがって

-   研究継続性
-   商用品質の統一感
-   再現性
-   説明可能性

を優先する。

------------------------------------------------------------------------

# 16. Final Summary

GenesisPrediction v2 の UI System は、

``` text
共通レイアウト
+
各ページの明確な責務
+
read-only 表示原則
+
必要最小限の fallback
```

で構成される。

主要ページ

``` text
Home
Overlay
Sentiment
Digest
Prediction
Prediction History
```

共通部品

``` text
app.css
common/header.html
common/footer.html
common/layout.js
```

最重要原則

``` text
UI は表示のみ
UI は再計算しない
UI は source of truth を作らない
```

------------------------------------------------------------------------

END OF DOCUMENT
