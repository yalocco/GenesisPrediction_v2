# AI Start Guide

GenesisPrediction v2

This document provides the entry point for AI systems interacting with the GenesisPrediction repository.

If you are an AI reading this repository, start here.

---

# Purpose

GenesisPrediction is a structured intelligence system designed to analyze world events and generate explainable predictions.

The system transforms raw data into predictions through multiple analytical layers.

This document helps AI understand:

- the repository structure
- where important documentation is located
- how the prediction system works
- how to safely assist development

---

# System Overview

GenesisPrediction uses a layered interpretation architecture.

```

Observation
↓
Trend
↓
Signal
↓
Early Warning
↓
Scenario
↓
Prediction

```

Predictions are never produced directly from raw data.

Instead, the system interprets the world step-by-step.

---

# Repository Structure

Main directories:

```

analysis/
scripts/
app/
docs/
data/

```

Explanation:

analysis  
Generated analytical artifacts and system outputs.  
This directory acts as the **Single Source of Truth (SST)** for system state.

scripts  
Execution engines and pipeline scripts.

app  
User interface dashboards.

docs  
System documentation and architecture.

data  
External datasets and reference data.

---

# Documentation Map

The documentation is organized by purpose.

```

docs/core
docs/active
docs/reference
docs/runbook
docs/ADR
docs/archive
docs/obsolete

```

Each folder has a specific role.

---

# Key Documents for AI

Start with these documents to understand the system.

1.

```

docs/ARCHITECTURE.md

```

High-level system architecture.

2.

```

docs/active/genesis_system_map.md

```

Overall system map.

3.

```

docs/active/prediction_architecture.md

```

Prediction engine design.

4.

```

docs/active/pipeline_system.md

```

Pipeline execution model.

5.

```

docs/core/genesis_brain.md

```

Core design philosophy.

---

# Prediction System

The prediction system consists of several engines.

```

trend_engine
signal_engine
scenario_engine
prediction_engine

```

Each engine processes outputs from the previous layer.

The layered model ensures predictions remain explainable.

---

# Morning Ritual

GenesisPrediction runs a daily automation pipeline called the **Morning Ritual**.

This process performs:

- data collection
- analysis generation
- prediction pipeline execution
- artifact publishing

Runbooks describing the process are located in:

```

docs/runbook/

```

---

# AI Interaction Principles

When assisting development:

Follow these guidelines.

1.

Respect the layered architecture.

Do not bypass system layers when proposing changes.

2.

Prefer stable deterministic pipelines.

Avoid introducing unnecessary complexity.

3.

Preserve explainability.

Predictions must be interpretable.

4.

Use existing documentation structure.

New documents should be placed in the correct folder.

---

# Documentation Rules

When creating new documentation:

```

Architecture → docs/core
Active design → docs/active
Operations → docs/runbook
Reference → docs/reference
Historical → docs/archive
Deprecated → docs/obsolete
Major decisions → docs/ADR

```

---

# Development Philosophy

GenesisPrediction prioritizes:

- structured reasoning
- layered interpretation
- explainable predictions
- modular system design

The goal is to build a reliable intelligence system capable of understanding global events.

---

# Summary

If you are an AI working with GenesisPrediction:

1.

Understand the layered architecture.

2.

Read the architecture documents.

3.

Respect the system structure.

4.

Assist development without breaking the architecture.

GenesisPrediction is designed to be both human-readable and AI-readable.
```
