# GenesisPrediction Data Contracts

Purpose

This document defines the official JSON artifact structures used by GenesisPrediction.

Artifacts act as **contracts between computation and UI**.

Changing these structures without updating all dependent components will break the system.

---

# sentiment_latest.json

Purpose

Stores aggregated news sentiment.

Structure

{
  "as_of": "YYYY-MM-DD",
  "positive": number,
  "neutral": number,
  "negative": number,
  "score": number
}

Used by

sentiment.html  
index.html

---

# daily_summary_latest.json

Purpose

Stores curated daily geopolitical summary.

Structure

{
  "as_of": "YYYY-MM-DD",
  "highlights": [
    {
      "title": "string",
      "summary": "string",
      "source": "string"
    }
  ]
}

Used by

digest.html

---

# view_model_latest.json

Purpose

Stores global macro situation summary.

Structure

{
  "as_of": "YYYY-MM-DD",
  "global_risk": "LOW | MEDIUM | HIGH",
  "economic_signals": [],
  "geopolitical_signals": []
}

Used by

index.html  
overlay.html

---

# scenario_latest.json

Purpose

Stores generated future scenarios.

Structure

{
  "as_of": "YYYY-MM-DD",
  "scenarios": [
    {
      "name": "string",
      "probability": number,
      "confidence": number,
      "drivers": [],
      "watchpoints": [],
      "invalidators": []
    }
  ]
}

Used by

prediction.html

---

# prediction_latest.json

Purpose

Stores final prediction output.

Structure

{
  "as_of": "YYYY-MM-DD",
  "dominant_scenario": "string",
  "confidence": number,
  "risk_level": "LOW | MEDIUM | HIGH",
  "summary": "string"
}

Used by

prediction.html  
prediction_history.html

---

# fx_decision_latest.json

Purpose

Stores FX remittance decision signals.

Structure

{
  "as_of": "YYYY-MM-DD",
  "pairs": {
    "USDJPY": "SEND | WAIT | CAUTION",
    "USDTHB": "SEND | WAIT | CAUTION",
    "JPYTHB": "SEND | WAIT | CAUTION"
  }
}

Used by

overlay.html

---

# Important Rule

Artifacts must remain backward compatible whenever possible.

If schema changes are necessary:

1. Update this document
2. Update all scripts generating the artifact
3. Update all UI pages reading the artifact

---

# Closing Note

Artifacts are the glue that connects GenesisPrediction layers.

Stable artifact contracts ensure that the system remains robust even as internal algorithms evolve.
```

---

# これで石板は5枚

GenesisPrediction **Architectural Tablets**

1️⃣ UI構造

```
docs/ui/ui_pages_reference.md
```

2️⃣ パイプライン

```
docs/architecture/pipeline_overview.md
```

3️⃣ システム地図

```
docs/architecture/system_map.md
```

4️⃣ 憲法

```
docs/constitution/genesis_architecture_rules.md
```

5️⃣ データ契約

```
docs/architecture/data_contracts.md
```
