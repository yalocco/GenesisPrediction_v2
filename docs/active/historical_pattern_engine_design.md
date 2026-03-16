# GenesisPrediction Historical Pattern Engine Design
Prediction Layer Phase5

---

# 1. Purpose

GenesisPrediction Phase5 introduces a **Historical Pattern Engine**.

The purpose is to integrate historical cause-effect analysis into the Prediction Layer.

Current GenesisPrediction pipeline:

Observation  
↓  
Trend  
↓  
Signal  
↓  
Scenario  
↓  
Prediction  

Phase5 extends this architecture by adding **Historical Pattern Intelligence**.

Observation  
↓  
Trend  
↓  
Signal  
↓  
Historical Pattern  
↓  
Scenario  
↓  
Prediction  

Historical knowledge improves Scenario generation and Prediction confidence.

GenesisPrediction evolves toward a **Civilization Pattern Analysis System**.

---

# 2. Core Concept

History often repeats **structural cause-effect chains**.

Typical structure:

Cause  
↓  
Trigger  
↓  
Event  
↓  
Impact  
↓  
Economic Outcome  
↓  
Civilization Outcome  

Examples:

War  
↓  
Resource consumption  
↓  
Fiscal deterioration  
↓  
Currency debasement  
↓  
Commodity inflation  

Drought  
↓  
Agricultural collapse  
↓  
Food shortage  
↓  
Grain price spike  
↓  
Social instability  

Empire overextension  
↓  
Military spending  
↓  
Fiscal crisis  
↓  
Political fragmentation  
↓  
Imperial decline  

The Historical Pattern Engine encodes these structures.

---

# 3. Engine Role in Prediction Layer

Historical Pattern Engine **does not replace Scenario Engine**.

Instead it **supports Scenario generation**.

Observation  
↓  
Trend Engine  
↓  
Signal Engine  
↓  
Historical Pattern Engine  
↓  
Scenario Engine  
↓  
Prediction Engine  

Responsibilities:

## Historical Pattern Engine

- Identify matching historical patterns
- Detect cause-effect structures
- Provide scenario bias
- Provide stress indicators
- Provide watchpoints derived from historical analogs

## Scenario Engine

- Generate future scenarios
- Use signals + historical context
- Integrate historical stress and expected outcomes

## Prediction Engine

- Produce final prediction summary
- Reflect scenario confidence informed by historical context

---

# 4. Architecture Principles

The engine follows GenesisPrediction architecture rules.

Key rules:

## UI

Display only

## Scripts

Calculation logic only

## Analysis

Single Source of Truth (SST)

Historical Pattern analysis must be stored in the **analysis layer**.

UI must never calculate historical matching.

Historical Pattern logic belongs to:

- scripts/
- analysis/

and never to UI rendering code.

---

# 5. Data Location

Historical pattern libraries are stored in:

```text
analysis/historical/
````

Initial library files:

```text
analysis/historical/
war_patterns.json
financial_crisis_patterns.json
empire_decline_patterns.json
disaster_patterns.json
```

These files represent the **Historical Pattern Library**.

They are maintained as structured knowledge artifacts.

Daily engine outputs are stored in:

```text
analysis/prediction/
historical_pattern_latest.json
historical_analog_latest.json
```

History snapshots are stored in:

```text
analysis/prediction/history/YYYY-MM-DD/
historical_pattern.json
historical_analog.json
```

---

# 6. Pattern Categories

Initial pattern categories:

## War Patterns

Examples:

* Major war mobilization
* Proxy wars
* Resource wars
* Total war economies
* Sanctions escalation with military confrontation

Typical impacts:

* Energy shock
* Fiscal deterioration
* Currency pressure
* Commodity inflation
* Trade route disruption

---

## Financial Crisis Patterns

Examples:

* Banking collapse
* Debt crisis
* Currency crisis
* Asset bubble burst
* Liquidity freeze

Typical impacts:

* Credit contraction
* Currency collapse
* Asset deflation
* Recession
* Political dissatisfaction

---

## Empire Decline Patterns

Examples:

* Imperial overstretch
* Political fragmentation
* Military exhaustion
* Elite corruption
* Administrative overexpansion

Typical impacts:

* Fiscal collapse
* Military defeat
* Political instability
* Territorial fragmentation
* Loss of legitimacy

---

## Disaster Patterns

Examples:

* Drought
* Flood
* Famine
* Pandemic
* Earthquake-driven supply collapse

Typical impacts:

* Food shortage
* Population shock
* Migration
* Social unrest
* Governance stress

---

# 7. Pattern Schema

Each pattern uses a common schema.

```json
{
  "schema_version": "1.0",
  "pattern_id": "string",
  "name": "string",
  "category": "war | finance | empire | disaster",
  "summary": "string",

  "cause_tags": [],
  "trigger_tags": [],

  "event_chain": [],
  "impact_chain": [],

  "economic_outcomes": [],
  "political_outcomes": [],
  "civilization_outcomes": [],

  "stress_vector": {
    "food_stress": 0.0,
    "energy_stress": 0.0,
    "fiscal_stress": 0.0,
    "currency_stress": 0.0,
    "trade_stress": 0.0,
    "political_stress": 0.0,
    "military_stress": 0.0,
    "social_unrest_stress": 0.0
  },

  "watchpoints": [],

  "analog_examples": [],

  "scenario_bias": {
    "best_case": 0.0,
    "base_case": 0.0,
    "worst_case": 0.0
  },

  "confidence_weight": 0.0,

  "notes": "string"
}
```

Schema intent:

* `cause_tags` = root drivers
* `trigger_tags` = immediate catalysts
* `event_chain` = chronological structural sequence
* `impact_chain` = downstream consequences
* `economic_outcomes` = market and macro effects
* `political_outcomes` = regime and governance effects
* `civilization_outcomes` = long-arc structural effects
* `stress_vector` = normalized civilizational stress representation
* `watchpoints` = real-time monitoring items for current comparison
* `analog_examples` = linked historical references
* `scenario_bias` = branch tendency contribution
* `confidence_weight` = trust level of this pattern in scoring

---

# 8. Historical Analog Concept

Historical Pattern and Historical Analog are related but different.

## Historical Pattern

Abstract cause-effect structure.

Examples:

* war → fiscal deterioration → currency weakness
* drought → food shortage → unrest
* debt bubble → banking collapse → recession

## Historical Analog

A concrete historical example of one or more patterns.

Examples:

* 1970s Oil Shock
* Late Roman Overextension
* 2008 Global Financial Crisis
* Bronze Age Collapse

Pattern = abstract structure
Analog = historical case

This distinction allows GenesisPrediction to compare both:

* structural similarity
* historical precedent similarity

---

# 9. Pattern Matching Logic

Historical Pattern Engine compares current signals with historical patterns.

Matching factors:

* Signal tag overlap
* Trend direction overlap
* Stress vector similarity
* Category match
* Economic outcome similarity
* Optional keyword overlap from observation summaries

Example scoring model:

```text
match_score =
  0.30 * signal_overlap
+ 0.20 * trend_overlap
+ 0.20 * stress_similarity
+ 0.20 * category_match
+ 0.10 * outcome_overlap
```

Highest score patterns become **dominant historical context**.

The scoring model in v1 should remain rule-based and explainable.

The goal is not black-box prediction.

The goal is interpretable structural matching.

---

# 10. Engine Inputs

Historical Pattern Engine reads from existing Prediction Layer artifacts and historical libraries.

Primary inputs:

```text
analysis/prediction/trend_latest.json
analysis/prediction/signal_latest.json
analysis/historical/war_patterns.json
analysis/historical/financial_crisis_patterns.json
analysis/historical/empire_decline_patterns.json
analysis/historical/disaster_patterns.json
```

Optional future inputs:

```text
analysis/world_politics/daily_summary_latest.json
analysis/world_politics/sentiment_latest.json
analysis/world_politics/view_model_latest.json
```

The engine must not depend on UI files.

---

# 11. Engine Outputs

Engine output artifacts:

```text
analysis/prediction/
historical_pattern_latest.json
historical_analog_latest.json
```

History snapshots:

```text
analysis/prediction/history/YYYY-MM-DD/
historical_pattern.json
historical_analog.json
```

## historical_pattern_latest.json example

```json
{
  "as_of": "YYYY-MM-DD",
  "engine_version": "v1",
  "dominant_pattern": "pattern_id",
  "pattern_confidence": 0.0,
  "matched_patterns": [
    {
      "pattern_id": "string",
      "category": "string",
      "match_score": 0.0,
      "matched_signals": [],
      "watchpoints": [],
      "expected_outcomes": [],
      "stress_profile": {}
    }
  ],
  "summary": "string"
}
```

## historical_analog_latest.json example

```json
{
  "as_of": "YYYY-MM-DD",
  "engine_version": "v1",
  "dominant_analog": "analog_id",
  "analog_confidence": 0.0,
  "top_analogs": [
    {
      "analog_id": "string",
      "title": "string",
      "match_score": 0.0,
      "similarities": [],
      "differences": [],
      "historical_outcomes": [],
      "scenario_bias": {}
    }
  ],
  "summary": "string"
}
```

---

# 12. Scenario Engine Integration

Scenario Engine receives additional inputs:

* Trend signals
* Signal drivers
* Historical patterns
* Historical analogs
* Stress indicators
* Analog-derived watchpoints

Scenario generation therefore becomes:

Signal-driven
+
History-informed

This improves scenario realism and explainability.

Scenario Engine should use Historical Pattern outputs for:

* scenario branch weighting
* watchpoint expansion
* expected downstream effects
* confidence adjustment

Historical Pattern Engine is therefore an **input layer** to Scenario Engine, not a replacement layer.

---

# 13. Prediction Engine Integration

Prediction Engine remains the final summary layer.

Historical Pattern Engine should not dominate Prediction.

Instead Prediction Engine should consume:

* dominant historical pattern
* dominant historical analog
* historical support level
* historical watchpoints
* historical stress summary

This allows Prediction to explain:

* why current conditions resemble past structures
* what outcomes history suggests
* where current conditions differ from prior analogs

Historical context strengthens explanation, not determinism.

---

# 14. Stress Vector Design

A common stress model is necessary across all pattern categories.

Initial stress dimensions:

* food_stress
* energy_stress
* fiscal_stress
* currency_stress
* trade_stress
* political_stress
* military_stress
* social_unrest_stress

These are normalized values from 0.0 to 1.0.

Purpose:

* unify comparison across categories
* enable rule-based similarity scoring
* prepare future civilization stress metrics

This vector is more important in v1 than complex market ratios.

---

# 15. Future Extensions

Planned future enhancements:

## Historical Analog Library

Examples:

* Roman Empire decline
* 1970s Oil Shock
* 2008 Financial Crisis
* Late Bronze Age Collapse
* Asian Financial Crisis 1997
* Weimar Inflation

## Civilization Stress Metrics

Possible indicators:

* Gold / Grain ratio
* Food / Wage ratio
* Debt / GDP stress
* Trade disruption metrics
* Reserve depletion ratio

## Cause-Effect Graph

Future version may formalize pattern relationships as graph structures.

Example:

* node = cause/event/impact/outcome
* edge = directional historical relationship

## Machine Learning

Future versions may use ML for pattern similarity detection.

However v1 should remain rule-based and interpretable.

---

# 16. Phase5 Implementation Steps

## Step 1

Design Historical Pattern Library schema.

Target files:

```text
analysis/historical/
war_patterns.json
financial_crisis_patterns.json
empire_decline_patterns.json
disaster_patterns.json
```

## Step 2

Populate initial patterns for each category.

## Step 3

Implement `scripts/historical_pattern_engine.py`.

## Step 4

Generate:

```text
analysis/prediction/historical_pattern_latest.json
analysis/prediction/historical_analog_latest.json
```

## Step 5

Integrate Historical Pattern outputs into Scenario Engine.

## Step 6

Expose summarized historical context in Prediction Engine outputs.

---

# 17. Final Vision

GenesisPrediction evolves into a system that integrates:

Historical Pattern
↓
Current Observation
↓
Future Scenario

The long-term goal is a **Civilization Pattern Analysis System**.

History is not prediction.

But **historical structures reveal the forces shaping the future**.

---

# 18. Future Phase Candidate — Historical Analog Engine

After Phase5 establishes the Historical Pattern Library,
the next natural evolution of GenesisPrediction is the
**Historical Analog Engine**.

Purpose:

Detect which historical periods or events most closely resemble
current global conditions.

Conceptual pipeline:

Historical Pattern Library
+
Current Observation
+
Trend
+
Signal
↓
Historical Analog Engine
↓
Scenario Engine
↓
Prediction

The Historical Analog Engine compares the present state of the
world with historical cause-effect structures stored in the
Historical Pattern Library.

The system searches for **structural similarity** across eras.

Examples of possible analog outputs:

1970s Oil Shock  
Late Roman Empire decline  
Pre-WWI geopolitical tension  
Late Bronze Age Collapse  

Analog detection helps answer a key question:

"What historical situation does the present world most resemble?"

This provides additional context for scenario generation.

Important principle:

Historical Analog Engine does not replace Scenario Engine.

Instead it **enhances Scenario realism** by supplying
historical reference points.

Possible output artifact:

analysis/prediction/historical_analog_latest.json

Future implementation phases may include:

Phase6-A  
Analog similarity scoring model

Phase6-B  
Historical analog candidate ranking

Phase6-C  
Integration with Scenario Engine weighting

Phase6-D  
Explanation layer for scenario interpretation

The Historical Pattern Engine therefore forms the
**knowledge foundation**, while the Historical Analog Engine
becomes the **interpretation layer**.

Together they support GenesisPrediction's long-term goal:

Civilization Pattern Analysis.

```
