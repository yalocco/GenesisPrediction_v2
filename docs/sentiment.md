# Sentiment分析仕様（GenesisPrediction v2）

## 目的
本仕様は、日次ニュースを **感情（Sentiment）スコア** に変換し、
世界情勢・金融市場・歴史的イベントと **時間軸で重ねて観測可能にする** ことを目的とする。

本Sentimentは「未来を当てる指標」ではなく、
**世界の温度変化を定量化し、予測を補助する観測層**である。

---

## 設計思想（重要）

### 1. 感情は「集団的ノイズ」として扱う
- 個別記事の主張や真偽は評価しない
- ニュース全体が発する“雰囲気”を数値化する

### 2. LLM依存を避け、まずは辞書ベースで安定運用
- 毎日必ず再現できることを最優先
- 将来、LLMスコアを **上書きレイヤー** として追加可能

---

## 対象データ

入力：
```
data/world_politics/daily_news_YYYY-MM-DD.json
```

- headline
- summary / content
- category

---

## 感情軸の定義（v1）

### Risk（恐怖・不安）
- war, attack, sanctions, crisis, recession, collapse, default, inflation, conflict

### Positive（楽観・安定）
- agreement, deal, recovery, growth, cooperation, stabilize, peace

### Uncertainty（不確実性）
- may, could, unclear, uncertain, likely, possibility

---

## スコア算出方法

### 記事単位

```
risk_score = risk_hits / token_count
positive_score = positive_hits / token_count
uncertainty_score = uncertainty_hits / token_count
```

### 日次集約

```
daily_risk = mean(risk_score)
daily_positive = mean(positive_score)
daily_uncertainty = mean(uncertainty_score)
```

---

## 出力ファイル

### 日次JSON（詳細）
```
data/world_politics/analysis/sentiment_YYYY-MM-DD.json
```

### 時系列CSV（GUI用）
```
data/world_politics/analysis/sentiment_timeseries.csv
```

列例：
- date
- risk
- positive
- uncertainty

---

## 可視化方針

### グラフ構成

1. 上段：Sentiment 時系列（risk / uncertainty）
2. 下段：為替 or 市場指標（USDJPY / JPYTHB 等）

- 二軸表示可
- Sentiment は **先行指標として解釈**

---

## 解釈ルール（固定）

- 急騰 = 危機の"気配"
- 高止まり = 構造的緊張
- 価格が動かなくても異常ではない

---

## 運用ルーティーン

1. daily news 取得
2. sentiment 生成
3. GUI で当日値と推移を確認
4. FX / Digest と併読

---

## 将来拡張（v2以降）

- LLMによる感情分類
- カテゴリ別 Sentiment（政治 / 経済 / 軍事）
- 歴史イベント（政変・戦争）との重ね描画

---

## 結論

Sentiment分析は、
GenesisPrediction v2 における **「未来を感じ取る層」**である。

価格や事件の前に動く"空気"を捉え、
驚かないための観測装置として機能する。

---

(GenesisPrediction v2 / Sentiment Spec v1)

