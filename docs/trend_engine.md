# Trend Engine
GenesisPrediction v2

Status: Active  
Purpose: 時系列変化を抽出する Trend Engine の設計  
Last Updated: 2026-03-07

---

# 0. Purpose

Trend Engine は


Observation Memory


から


時系列変化


を抽出するエンジンである。

目的

- 世界の変化の方向を検出する
- 持続・加速・反転を識別する
- Signal Engine の入力を生成する

Trend Engine は


未来予測


ではない。

役割は


世界の流れを理解すること


である。

---

# 1. Position in System

Prediction Layer の構造


Observation Memory
↓
Trend Engine
↓
Signal Engine
↓
Scenario Engine
↓
Prediction Engine


Trend Engine は


時系列理解レイヤ


である。

---

# 2. Input Data

Trend Engine は


analysis/


および


history/


を読む。

主な入力


analysis/world_politics/sentiment_latest.json
analysis/world_politics/daily_summary_latest.json
analysis/health_latest.json
analysis/fx/*


将来


analysis/history/YYYY-MM-DD/


を使用する。

---

# 3. Trend Definition

Trend は以下の要素で定義される。


direction
strength
duration
slope
momentum


意味

| field | meaning |
|------|--------|
direction | 上昇 / 下降 / 横ばい |
strength | 強度 |
duration | 継続日数 |
slope | 傾き |
momentum | 加速度 |

---

# 4. Trend Types

Trend Engine が検出する主要 Trend


increase
decrease
stable
reversal
acceleration
volatility


説明

### increase

継続的な上昇

### decrease

継続的な下降

### stable

変化なし

### reversal

方向転換

### acceleration

急激な変化

### volatility

変動拡大

---

# 5. Trend Domains

GenesisPrediction は複数ドメインを扱う。

Trend Engine はドメイン別に Trend を計算する。

主要ドメイン


world_politics
sentiment
fx
health
risk


例


world_politics sentiment rising
fx volatility expanding
health warnings increasing


---

# 6. Time Windows

Trend は複数の時間窓で計算する。


3d
7d
30d


意味


短期
中期
長期


例


3d trend = sudden spike
7d trend = emerging pattern
30d trend = structural shift


---

# 7. Trend Calculation

Trend は以下を計算する。


moving average
rate of change
standard deviation


計算要素

### Moving Average

平均値

### Rate of Change

変化速度

### Standard Deviation

変動幅

---

# 8. Trend Score

Trend Engine は


trend_score


を生成する。

範囲


-1.0 ～ +1.0


意味

| score | meaning |
|------|--------|
-1 | 強い下降 |
-0.5 | 下降 |
0 | 中立 |
0.5 | 上昇 |
1 | 強い上昇 |

---

# 9. Trend Output

Trend Engine の出力


trend_latest.json


---

# 10. Example Output

```json
{
  "as_of": "2026-03-07",
  "window": "7d",
  "domains": {
    "sentiment": [
      {
        "metric": "negative",
        "direction": "increase",
        "score": 0.72,
        "duration": 5,
        "slope": 0.11,
        "momentum": 0.09,
        "summary": "negative sentiment rising for 5 days"
      }
    ],
    "fx": [
      {
        "metric": "volatility",
        "direction": "increase",
        "score": 0.61,
        "duration": 3,
        "summary": "fx volatility expanding"
      }
    ]
  }
}
11. Trend → Signal Bridge

Trend Engine の出力は

Signal Engine

へ渡される。

Signal Engine は

閾値
持続時間
異常検出

を基準に

Signal

を生成する。

12. Design Principles

Trend Engine の原則

Principle 1

Trend は

未来予測ではない
Principle 2

Trend は

観測の要約

である。

Principle 3

Trend は

複数時間窓

で見る。

Principle 4

Trend は

ドメイン別

に計算する。

13. Future Expansion

将来追加予定

pattern similarity
regime detection
historical analog matching

これにより

Trend → Signal → Scenario

の精度が向上する。

14. Final Role

Trend Engine は

GenesisPrediction の感覚器

である。

役割

世界の変化を感じ取る

その後

Signal Engine

が

意味を解釈する

END OF DOCUMENT