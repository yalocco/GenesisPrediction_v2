# Early Warning Engine Design

GenesisPrediction v2

Purpose
- Detect early signals of systemic change
- Escalate risk conditions before full scenario shift
- Provide structured alerts to Scenario Layer
- Stabilize Prediction Layer responsiveness

Early Warning Engine sits between:

Signal Layer
and
Scenario Layer

Pipeline position

Observation
↓
Trend
↓
Signal
↓
Early Warning Engine
↓
Scenario
↓
Prediction

---

## Design Philosophy

Prediction should never react too late.

Therefore GenesisPrediction introduces a dedicated Early Warning Engine.

Goals:

- detect structural changes early
- escalate risk levels
- update scenario probabilities
- notify Prediction Layer

Early Warning does NOT create predictions.

It modifies **scenario weighting**.

---

## Input Sources

Early Warning consumes:

Signal Layer output

Example file

```

analysis/signal/signal_latest.json

```

Signal examples:

- geopolitical escalation
- monetary tightening
- commodity shock
- systemic financial stress
- currency volatility

Signals must already be normalized.

Early Warning does not perform raw data analysis.

---

## Core Concept

Each signal carries:

- strength
- direction
- persistence

The Early Warning Engine monitors:

```

signal intensity
signal persistence
multi-signal convergence

```

When thresholds are crossed:

```

warning_state = ON

```

---

## Warning Levels

Three warning levels exist.

### LEVEL 0 — Normal

No structural concern.

System continues standard Scenario evaluation.

```

warning_level = 0

```

---

### LEVEL 1 — Watch

Weak signals detected.

Monitoring increases.

```

warning_level = 1

```

Effects:

- Scenario watchpoints activated
- Probability adjustments small
- No prediction change yet

---

### LEVEL 2 — Escalation

Multiple signals converge.

```

warning_level = 2

```

Effects:

- Scenario probabilities recalculated
- Risk flags raised
- Prediction layer alerted

---

### LEVEL 3 — Systemic Risk

Structural regime change possible.

```

warning_level = 3

```

Effects:

- Worst case scenario weighting increases
- Prediction confidence reduced
- Alert visible in UI

---

## Multi-Signal Convergence

Early Warning reacts strongly when multiple signals align.

Example:

```

geopolitics escalation
+
oil supply shock
+
currency volatility

```

This produces stronger escalation.

Single signals rarely produce Level 3.

---

## Persistence Filter

Short term noise must not trigger warnings.

Therefore:

Signals must persist across multiple observation cycles.

Example:

```

signal_days >= 3

```

before escalation.

---

## Output Artifact

Early Warning produces:

```

analysis/prediction/early_warning_latest.json

````

Example schema:

```json
{
  "as_of": "2026-03-10",
  "warning_level": 2,
  "active_signals": [
    "geopolitical_escalation",
    "oil_supply_risk"
  ],
  "signal_count": 2,
  "persistence_days": 4,
  "risk_direction": "global_risk_up",
  "notes": "multiple geopolitical stress signals detected"
}
````

---

## Scenario Integration

Scenario Layer consumes Early Warning output.

Example:

```
analysis/prediction/early_warning_latest.json
```

Scenario engine adjusts probabilities:

Example:

```
best_case   ↓
base_case   →
worst_case  ↑
```

Adjustment magnitude depends on warning level.

---

## Prediction Integration

Prediction Layer reads:

```
early_warning_latest.json
```

and integrates warning state into prediction output.

Example fields:

```
overall_risk
confidence
dominant_scenario
```

High warning levels reduce confidence.

---

## UI Integration

Early Warning appears in Prediction UI.

Example display:

```
Early Warning Status

Level 0 — Normal
Level 1 — Watch
Level 2 — Escalation
Level 3 — Systemic Risk
```

UI should visualize:

* warning level
* active signals
* risk direction

---

## Safety Design

Early Warning must avoid false positives.

Mechanisms:

* persistence filters
* multi-signal requirement
* scenario confirmation

Prediction must never flip violently from single signals.

---

## Runtime Integration

Early Warning executes during Morning Ritual.

Execution order:

```
Signal generation
↓
Early Warning evaluation
↓
Scenario generation
↓
Prediction synthesis
```

Early Warning must run before Scenario Layer.

---

## Future Extensions

Possible improvements:

* historical signal comparison
* regime detection
* volatility shock detection
* macroeconomic divergence analysis

These can increase Early Warning accuracy.

---

## Summary

Early Warning Engine provides:

* early detection of systemic change
* scenario probability adjustments
* risk escalation alerts

Without Early Warning:

Prediction becomes reactive.

With Early Warning:

Prediction becomes anticipatory.

This component is a core pillar of GenesisPrediction.

```
