# Signal Engine
GenesisPrediction v2

Status: Active
Purpose: Trend から意味のある兆候（Signal）を抽出する Signal Engine の設計
Last Updated: 2026-03-07

---

# 0. Purpose

Signal Engine は


Trend


から


意味のある兆候


を検出するエンジンである。

Trend が


世界の流れ


であるのに対し、

Signal は


注意すべきイベント


を表す。

目的

- Trend を Early Warning Signal に変換する
- 重要な変化を検出する
- Scenario Engine の入力を生成する

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


Signal Engine は


兆候検知レイヤ


である。

---

# 2. Input

Signal Engine は


trend_latest.json


を入力として使用する。

Trend Engine が出力する


trend direction
trend score
duration
momentum


などの情報を分析する。

---

# 3. Signal Definition

Signal は


異常
持続
急変
構造変化


などの


重要な変化


を意味する。

Signal は


Scenario Engine


の入力として使用される。

---

# 4. Signal Types

Signal Engine が生成する主な Signal


persistence
acceleration
reversal
anomaly
regime_shift
volatility_expansion


説明

### persistence

一定期間以上継続する Trend

例


negative sentiment rising for 5 days


---

### acceleration

Trend の速度が増加

例


risk score rapidly increasing


---

### reversal

Trend の方向が反転

例


sentiment turning negative


---

### anomaly

統計的異常

例


sudden spike in war coverage


---

### regime_shift

構造変化

例


geopolitical narrative shift


---

### volatility_expansion

変動拡大

例


FX volatility surge


---

# 5. Signal Detection Rules

Signal Engine は


threshold
duration
momentum


を基準に Signal を検出する。

例

### Persistence Rule


trend_duration >= 5 days


→ persistence signal

---

### Acceleration Rule


momentum > threshold


→ acceleration signal

---

### Reversal Rule


direction change


→ reversal signal

---

### Anomaly Rule


z-score > threshold


→ anomaly signal

---

# 6. Signal Severity

Signal は重要度を持つ。


low
medium
high
critical


決定要素


trend strength
duration
domain importance


---

# 7. Signal Confidence

Signal は


confidence


を持つ。

範囲


0.0 ～ 1.0


計算要素


trend consistency
data reliability
multi-domain confirmation


---

# 8. Signal Domains

Signal はドメイン別に生成される。

主要ドメイン


world_politics
sentiment
fx
health
risk


例


sentiment persistence
fx volatility expansion
health warnings increase


---

# 9. Signal Output

Signal Engine の出力


signal_latest.json


保存先


analysis/prediction/


---

# 10. Example Output

```json
{
  "as_of": "2026-03-07",
  "signals": [
    {
      "id": "SIG-SENT-001",
      "type": "persistence",
      "domain": "sentiment",
      "severity": "medium",
      "confidence": 0.74,
      "source_trend": "negative sentiment",
      "duration": 5,
      "summary": "Negative sentiment has persisted for 5 days"
    },
    {
      "id": "SIG-FX-002",
      "type": "volatility_expansion",
      "domain": "fx",
      "severity": "high",
      "confidence": 0.68,
      "summary": "FX volatility expanding rapidly"
    }
  ]
}
11. Signal → Scenario Bridge

Signal Engine の出力は

Scenario Engine

に渡される。

Scenario Engine は

複数 Signal

を統合し

未来分岐

を生成する。

12. Design Principles

Signal Engine の原則

Principle 1

Signal は

Trend の意味解釈

である。

Principle 2

Signal は

Early Warning System

として機能する。

Principle 3

Signal は

説明可能

でなければならない。

Principle 4

Signal は

複数ドメイン

で確認されると強くなる。

13. Future Expansion

将来追加予定

multi-domain signal fusion
risk propagation
event clustering
historical signal matching

これにより

Scenario Engine

の精度が向上する。

14. Final Role

Signal Engine は

GenesisPrediction の警報装置

である。

役割

危険の兆候を早く検出する

その後

Scenario Engine

が

未来の展開

を生成する。

END OF DOCUMENT