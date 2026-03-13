# GenesisPrediction Artifact Map

GenesisPrediction では  
複数の pipeline が JSON artifact を生成し、  
UI はそれらを read-only で参照する。

このドキュメントは

- どの script が
- どの JSON / PNG / CSV を生成し
- どの UI がそれを読むか

を整理するための実務用マップである。

---

# 1. 基本原則

## 1.1 Single Source of Truth

GenesisPrediction UI は **read-only** とし、  
UI 側で再計算しない。

計算・集約・正規化は script / pipeline 側で行い、  
UI は生成済み artifact を読む。

---

## 1.2 latest artifact の考え方

`latest` は表示用の最新成果物である。  
ただし latest は責務を混線させない。

- Digest latest
- World latest
- Sentiment latest
- FX latest
- Prediction latest

は別物として扱う。

---

## 1.3 調査の基本順序

UI 表示がおかしい場合は以下の順で確認する。

1. artifact が存在するか  
2. artifact の更新時刻が新しいか  
3. 生成 script が実行されたか  
4. refresh_latest_artifacts が正しいコピーをしたか  
5. UI の fetch path が正しいか

---

# 2. World Politics 系

## 2.1 raw news

### 役割
NewsAPI / analyzer が取得した生ニュース。

### 主ファイル
- `data/world_politics/YYYY-MM-DD.json`

### 例
- `data/world_politics/2026-03-13.json`

### 主な内容
- `articles[]`
- `title`
- `description`
- `url`
- `urlToImage`
- `publishedAt`
- `source.name`

### 主な利用先
- `scripts/build_daily_sentiment.py`
- `scripts/build_world_view_model_latest.py`

---

## 2.2 analyzer latest

### 役割
analyzer が作る latest pointer / summary 系。

### 主ファイル
- `data/world_politics/analysis/latest.json`
- `data/world_politics/analysis/summary.json`
- `data/world_politics/analysis/anchors.json`
- `data/world_politics/analysis/diff_YYYY-MM-DD.json`

### 主な script
- docker analyzer
- `scripts/run_daily_with_publish.ps1`

---

## 2.3 daily_news_latest

### 役割
world analysis 側の latest alias。

### 主ファイル
- `data/world_politics/analysis/daily_news_latest.json`
- `data/world_politics/analysis/daily_news_YYYY-MM-DD.json`

### 注意
この JSON は縮約 alias であり、  
raw article 全体を持たない場合がある。

そのため article 単位処理では  
まず raw `data/world_politics/YYYY-MM-DD.json` を優先する。

---

## 2.4 daily_summary_latest

### 役割
World summary 表示用の latest summary。

### 主ファイル
- `data/world_politics/analysis/daily_summary_latest.json`
- `data/world_politics/analysis/daily_summary_YYYY-MM-DD.json`

### 主な利用先
- Digest summary
- Global status summary 補助

---

# 3. Sentiment 系

## 3.1 sentiment_latest

### 役割
記事単位の sentiment 正規化結果。

### 生成 script
- `scripts/build_daily_sentiment.py`

### 入力
優先順は以下。

1. `data/world_politics/YYYY-MM-DD.json`
2. `data/world_politics/analysis/daily_news_YYYY-MM-DD.json`
3. `data/world_politics/analysis/daily_news_latest.json`

### 出力
- `data/world_politics/analysis/sentiment_latest.json`
- `data/world_politics/analysis/sentiment_YYYY-MM-DD.json`

### 主な内容
- `items[]`
- `title`
- `url`
- `source`
- `description`
- `publishedAt`
- `image`
- `risk`
- `positive`
- `uncertainty`
- `net`
- `score`
- `sentiment`

### summary / today
- `today.articles`
- `today.risk`
- `today.positive`
- `today.uncertainty`
- `today.label_counts`
- `summary.positive`
- `summary.negative`
- `summary.neutral`
- `summary.mixed`
- `summary.unknown`

### 主な利用先
- `app/static/sentiment.html`
- `app/static/digest.html` の sentiment balance fallback

---

## 3.2 sentiment_timeseries

### 役割
sentiment trend の時系列。

### 主ファイル
- `data/world_politics/analysis/sentiment_timeseries.csv`

### 主な利用先
- `app/static/sentiment.html` 3-axis trend

---

# 4. World View Model 系

## 4.1 world_view_model_latest

### 役割
world article cards 用の正規化済み view model。

### 生成 script
- `scripts/build_world_view_model_latest.py`

### 入力
- `data/world_politics/analysis/latest.json`
- `data/world_politics/analysis/sentiment_latest.json`
- `data/world_politics/YYYY-MM-DD.json`

### 出力
実ファイル
- `data/world_politics/analysis/view_model_latest.json`

公開 alias
- `analysis/world_view_model_latest.json`

### 主な内容
- `sections[].cards[]`
- `title`
- `summary`
- `source`
- `url`
- `image`

### 主な利用先
- `app/static/sentiment.html`
- `app/static/digest.html`
- 将来の `overlay.html` 経済ニュース枠

### 注意
`view_model_latest.json` というファイル名が  
Digest latest と混線しやすい。

必要に応じて

- `world_view_model_latest.json`
- `digest_view_model_latest.json`

のような責務分離を検討する。

---

# 5. Digest 系

## 5.1 digest view latest

### 役割
Digest UI 用の summary / highlights / cards 表示用 view。

### 生成 script
- `scripts/build_digest_view_model.py`

### 出力候補
- `data/digest/view_model_latest.json`
- `data/digest/view/view_model_latest.json`
- `data/digest/view/YYYY-MM-DD.json`

### 主な利用先
- `app/static/digest.html`

### 注意
refresh_latest_artifacts において  
world view latest が digest latest を上書きしないようにする必要がある。

---

## 5.2 Digest UI で必要なもの

Digest page では最低限以下を使う。

- summary text
- topic tags
- highlights KPI
- article cards
- sentiment balance
- FX regime

### 参照元の基本
- Digest summary: `daily_summary_latest.json`
- Sentiment balance fallback: `sentiment_latest.json`
- Article cards: digest view または world view
- FX regime: `data/fx/fx_decision_latest.json` など

---

# 6. FX 系

## 6.1 FX chart / overlay 画像

### 主なファイル
- `data/fx/fx_jpy_thb_overlay.png`
- `data/fx/jpy_thb_remittance_overlay.png`
- `data/fx/fx_multi_overlay.png`

### publish 先
- `data/world_politics/analysis/fx_jpy_thb_overlay.png`
- `data/world_politics/analysis/fx_jpy_usd_overlay.png`
- その他 latest txt pointer

### 主な利用先
- `app/static/overlay.html`

---

## 6.2 FX decision latest

### 役割
FX regime / remittance decision の latest JSON。

### 現在確認済みファイル
- `data/fx/fx_decision_latest.json`

### 現状の問題
確認時点では

- `2026-01-31`
- 仮データ
- `fx_decision = wait`
- `fx_reasons = ["初期セットアップのための仮データ"]`

であり、本番値ではない。

### 想定される将来形
以下のような正式 latest artifact が必要。

- `data/fx/fx_decision_latest.json`
- `data/fx/fx_decision_latest_jpythb.json`
- `data/fx/fx_decision_latest_usdjpy.json`
- `data/fx/fx_decision_latest_usdthb.json`

### Digest / Overlay で期待する情報
- decision
- action
- pair
- reason

### 主な利用先
- `app/static/digest.html`
- `app/static/overlay.html`

---

# 7. Prediction 系

## 7.1 prediction pipeline

### 生成 script
- `scripts/run_prediction_pipeline.py`

### analysis latest
- `analysis/trend_latest.json`
- `analysis/signal_latest.json`
- `analysis/scenario_latest.json`
- `analysis/prediction_latest.json`
- `analysis/early_warning_latest.json`

### history
- `analysis/prediction_history/YYYY-MM-DD/trend.json`
- `analysis/prediction_history/YYYY-MM-DD/signal.json`
- `analysis/prediction_history/YYYY-MM-DD/scenario.json`
- `analysis/prediction_history/YYYY-MM-DD/prediction.json`
- `analysis/prediction_history/YYYY-MM-DD/early_warning.json`

### 主な利用先
- `app/static/prediction.html`
- `app/static/prediction_history.html`

---

# 8. analysis/ 直下 alias

### 役割
UI から読みやすい公開 alias。

### 例
- `analysis/daily_news_latest.json`
- `analysis/daily_summary_latest.json`
- `analysis/sentiment_latest.json`
- `analysis/world_view_model_latest.json`
- `analysis/health_latest.json`
- `analysis/trend_latest.json`
- `analysis/signal_latest.json`
- `analysis/scenario_latest.json`
- `analysis/prediction_latest.json`
- `analysis/early_warning_latest.json`

### 注意
`analysis/view_model_latest.json` は  
digest と world のどちらを指すか曖昧になりやすい。

可能なら将来的に明示名へ分離する。

---

# 9. Morning Ritual 系

## 9.1 エントリーポイント

- `scripts/run_morning_ritual.ps1`

### 主な中継
- `scripts/run_daily_with_publish.ps1`

### 流れ
1. analyzer
2. summary materialize
3. build daily sentiment
4. build world view model latest
5. build digest view model
6. prediction pipeline
7. FX lane
8. refresh latest artifacts

---

## 9.2 run_daily_with_publish.ps1

### 現在の重要ポイント
- `build_daily_sentiment.py` を呼ぶ
- `build_world_view_model_latest.py` を呼ぶ
- latest alias を publish する

### 注意
Digest latest と world latest を  
同じ `view_model_latest.json` 名で扱うと混線しやすい。

---

## 9.3 refresh_latest_artifacts.ps1

### 役割
latest artifact を

- dist deploy
- digest
- public alias

へコピーする。

### 現在の重要論点
- `world_politics/analysis/view_model_latest.json`
- `data/digest/view_model_latest.json`

の責務分離。

### 追加論点
- FX latest artifact も正式に refresh 対象へ入れる必要がある。

---

# 10. UI ごとの主参照先

## 10.1 Sentiment
- `analysis/sentiment_latest.json`
- `analysis/world_view_model_latest.json`
- `data/world_politics/analysis/sentiment_timeseries.csv`

---

## 10.2 Digest
- `data/digest/view_model_latest.json`
- `data/digest/view/view_model_latest.json`
- `data/world_politics/analysis/daily_summary_latest.json`
- `data/world_politics/analysis/sentiment_latest.json`
- `data/fx/fx_decision_latest.json`（現状は仮データ）

---

## 10.3 Overlay
- FX overlay png
- FX decision latest
- 将来: world/economy article cards

---

## 10.4 Prediction
- `analysis/prediction_latest.json`
- `analysis/scenario_latest.json`
- `analysis/signal_latest.json`
- `analysis/trend_latest.json`

---

## 10.5 Prediction History
- `analysis/prediction_history/YYYY-MM-DD/*.json`

---

# 11. 今回の調査で確定したこと

## 11.1 Sentiment
`sentiment_latest.json` は  
raw `data/world_politics/YYYY-MM-DD.json` を優先して生成することで正常化した。

---

## 11.2 World View
`build_world_view_model_latest.py` を Morning Ritual に接続することで  
最新 article cards が自動生成されるようになった。

---

## 11.3 Digest Sentiment Balance
Digest の sentiment balance は  
`sentiment_latest.json` を fallback として使うことで正常表示できる。

---

## 11.4 Digest FX Regime
Digest の FX Regime UI 枠は完成した。  
ただし参照元の `data/fx/fx_decision_latest.json` が仮データのままであり、  
artifact 側の正式接続が未完である。

---

# 12. 今後の整理対象

1. digest latest の入力元固定  
2. world latest artifact の正式名称整理  
3. refresh_latest_artifacts の責務分離  
4. FX latest artifact の正式生成  
5. Overlay 用 経済ニュース artifact の定義

---

# 13. Debugging checklist

## UI が崩れた時
- HTML を確認
- fetch path を確認
- JSON の shape を確認
- CSS クラス競合を確認

## 値が `—` の時
- JSON exists
- updated time
- key 名一致
- latest artifact が仮データではないか
- fallback path が存在するか

## Morning Ritual で確認する時
- sentiment_latest exists
- world_view_model_latest exists
- digest latest exists
- prediction latest exists
- FX latest exists
- refresh copied from correct source only

---

# 14. 運用メモ

GenesisPrediction は  
artifact 数が増えており、

- JSON
- PNG
- CSV
- latest alias
- dated artifact

が多層化している。

そのため、今後は

- artifact 名
- source of truth
- publish alias
- UI fetch path

を必ず分けて管理すること。