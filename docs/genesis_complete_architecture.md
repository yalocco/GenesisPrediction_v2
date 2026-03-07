# GenesisPrediction v2  
Complete System Architecture

This document describes the **complete architecture of GenesisPrediction v2**.

GenesisPrediction is not only a news analysis tool.  
It is a **world observation and prediction system** designed to:

- observe global events
- detect trends
- generate future scenarios
- track prediction drift over time

The system transforms raw information into structured insight and long-term memory.

---

# 1. System Overview

GenesisPrediction v2 is composed of six major layers.

```

Data Sources
↓
Processing Pipelines
↓
Runtime State (SST)
↓
Observation Memory
↓
Prediction System
↓
Visualization / Decision Support

```

The system is executed daily by the **Morning Ritual pipeline**.

---

# 2. Data Sources

The system collects multiple external signals.

Examples:

```

Global News (MediaStack / News APIs)
FX Market Data
Derived metrics
Manual signals

```

These inputs represent the **external state of the world**.

---

# 3. Processing Pipelines

Raw inputs are transformed by pipeline scripts.

Main components:

```

fetcher
analyzer
publish pipelines
FX pipelines
sentiment analysis
observation builders
prediction pipeline

```

Responsibilities:

```

collect data
clean data
analyze signals
generate summaries
publish latest artifacts

```

Execution is orchestrated by:

```

scripts/run_morning_ritual.ps1

```

---

# 4. Runtime State (Single Source of Truth)

The runtime state lives in:

```

analysis/

```

This directory represents the **current state of the world**.

Examples:

```

analysis/world_politics/
analysis/digest/
analysis/fx/
analysis/health/
analysis/sentiment/
analysis/prediction/

```

Important principle:

```

analysis = Single Source of Truth (SST)

```

The UI reads from this state but **never modifies it**.

---

# 5. Observation Memory

GenesisPrediction stores daily observations.

```

history/

```

Structure:

```

history/YYYY-MM-DD/

```

Typical artifacts:

```

daily_summary.json
sentiment.json
health.json
observation snapshots

```

Purpose:

```

track historical world states
enable trend analysis
detect long-term pattern changes

```

This layer transforms the system from **stateless analysis** to **historical intelligence**.

---

# 6. Prediction System

Prediction is built on top of observations.

Pipeline stages:

```

Trend Engine
↓
Signal Engine
↓
Scenario Engine
↓
Prediction Engine

```

Outputs are stored in:

```

analysis/prediction/

```

Artifacts include:

```

trend_latest.json
signal_latest.json
scenario_latest.json
prediction_latest.json

```

These represent the **current forecast state**.

---

# 7. Prediction Memory

Predictions are also stored historically.

Structure:

```

analysis/prediction/history/YYYY-MM-DD/

```

Files:

```

trend.json
signal.json
scenario.json
prediction.json

```

This allows the system to observe:

```

prediction drift
scenario evolution
confidence changes
risk changes

```

---

# 8. Prediction Index

To make historical data efficient for UI usage, an index is generated.

File:

```

analysis/prediction/prediction_history_index.json

```

Built by:

```

scripts/build_prediction_history_index.py

```

Purpose:

```

fast UI loading
time window slicing
trend visualization

```

Instead of scanning the filesystem, the UI reads the index.

---

# 9. Visualization Layer

The user interface lives in:

```

app/static/

```

Main pages:

```

index.html
overlay.html
sentiment.html
digest.html
prediction.html
prediction_history.html

```

Responsibilities:

```

visualize analysis state
visualize prediction state
visualize prediction memory
display drift and scenario evolution

```

Important rule:

```

UI is read-only.
All logic lives in scripts.

```

---

# 10. Morning Ritual Execution

The system is executed daily through the **Morning Ritual** pipeline.

Execution flow:

```

run_morning_ritual.ps1
↓
run_daily_with_publish.ps1
↓
data collection
analysis generation
sentiment build
FX pipelines
observation artifacts
health build
prediction pipeline
prediction memory save
prediction index build

```

After execution:

```

UI automatically reflects new state.

```

---

# 11. Conceptual Model

GenesisPrediction can be summarized as:

```

World Observation System
↓
Observation Memory
↓
Trend Intelligence
↓
Prediction Intelligence
↓
Prediction Memory
↓
Prediction Drift Visualization
↓
Human Decision Support

```

The system converts **raw information → structured understanding → future scenarios**.

---

# 12. System Philosophy

GenesisPrediction is built on several principles.

### Separation of Layers

```

data
processing
state
memory
prediction
visualization

```

Each layer has a clear responsibility.

---

### Single Source of Truth

```

analysis/

```

represents the current world state.

---

### Memory as Intelligence

Historical storage enables:

```

trend detection
pattern discovery
prediction drift analysis

```

---

### Human-Centered Insight

The final consumer of the system is the **human decision maker**.

The system supports:

```

risk awareness
scenario awareness
strategic thinking
financial defense decisions

```

---

# 13. Current System Status

GenesisPrediction v2 currently includes:

```

Observation System
Observation Memory
Prediction Engine
Prediction Memory
Prediction Drift Dashboard

```

The architecture now supports long-term expansion.

Future work may include:

```

advanced scenario engines
automated signal discovery
historical analog analysis
decision support automation

```

---

# 14. Final Summary

GenesisPrediction v2 is a system designed to:

```

observe the world
remember its changes
generate future scenarios
track prediction evolution
support human decision making

```

It is not simply a dashboard.

It is an **evolving intelligence system for understanding global dynamics**.
```
