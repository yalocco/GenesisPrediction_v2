# GenesisPrediction v2 — System History

Status: Active
Purpose: Architecture change log

---

# Philosophy

GenesisPrediction は

再現可能な研究システム

である。

そのため

**設計変更は必ず履歴として残す。**

---

# 2026-03

## Morning Ritual WorldDate 修正

変更内容

```

WorldDate
UTC yesterday
↓
LOCAL DATE

```

変更理由

ニュース raw データは

```

data/world_politics/YYYY-MM-DD.json

```

として **ローカル日付基準で保存される。**

旧仕様

```

WorldDate = UTC yesterday

```

では

```

missing raw news

```

エラーが発生することがあった。

新仕様

```

run_morning_ritual.ps1

```

引数無し実行時

```

WorldDate = LOCAL DATE

```

---

## 結果

Morning Ritual が

- 会社PC
- 自宅PC

両環境で安定完走。

---

# 2026-02

## Digest UI 完成

UI構成

```

Home
Overlay
Sentiment
Digest

```

Digest UI

```

Summary
KPI
Top highlights
Risk sort
Show-all default
Thumbnail

```

安定版完成。

---

## FX Multi Overlay

通貨ペア

```

JPY/THB
JPY/USD

```

Overlay構造

```

analysis/
fx_overlay_latest.png

```

---

# Future History

将来の変更は必ずここに追加する。

例

```

Prediction Engine v1
Trend3 evolution
Scenario engine

```

---

END OF DOCUMENT
```
