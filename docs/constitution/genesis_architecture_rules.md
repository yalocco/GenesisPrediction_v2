# GenesisPrediction Architecture Rules
(Constitution of the System)

Purpose

This document defines the **non-negotiable architectural rules** of GenesisPrediction.

These rules exist to protect the system from structural drift and accidental design violations.

Future developers, AI systems, and maintainers must follow these rules.

Breaking these rules may cause instability, hidden logic duplication, or system corruption.

This document acts as the **constitutional law** of the GenesisPrediction architecture.

---

# Principle 1  
Separation of Computation and Presentation

GenesisPrediction strictly separates computation from presentation.

Computation is allowed only in:

scripts/
analysis/

Presentation exists only in:

app/static/

The UI must never perform calculations.

The UI must only display results.

---

# Principle 2  
Analysis Directory is the Single Source of Truth (SST)

All final computed results must exist in:

analysis/

Examples:

analysis/world_politics/analysis/
analysis/fx/

Artifacts inside analysis are the **authoritative outputs of the system**.

The UI and other components must read from analysis rather than recomputing results.

---

# Principle 3  
Artifacts Are Contracts Between Layers

Artifacts connect the computation layer and presentation layer.

Examples:

sentiment_latest.json  
daily_summary_latest.json  
view_model_latest.json  
scenario_latest.json  
prediction_latest.json  

Artifacts must remain stable.

Changing artifact structures without updating the entire system may break the pipeline.

Artifacts are therefore considered **system contracts**.

---

# Principle 4  
Scripts Generate Artifacts

Only scripts may generate or update artifacts.

Examples of scripts:

build_daily_sentiment.py  
build_world_view_model_latest.py  
scenario_engine.py  
prediction_engine.py  
fx_multi_overlay_from_rates.py  
build_fx_overlay_variants.py  

Scripts must be deterministic and reproducible.

---

# Principle 5  
UI Must Remain Passive

UI pages must never:

- calculate predictions
- recompute FX overlays
- generate signals
- transform analysis data

UI pages must only:

- read artifacts
- render charts
- display summaries

UI errors must never affect analysis results.

---

# Principle 6  
Morning Ritual Is the System Entry Point

Daily system execution begins with:

scripts/run_morning_ritual.ps1

This script orchestrates the pipeline:

fetch
↓
observation
↓
trend
↓
signal
↓
scenario
↓
prediction
↓
artifact refresh

All daily system updates must flow through this pipeline.

---

# Principle 7  
Prediction Is the Final Layer

The architecture follows a layered structure.

Observation  
↓  
Trend  
↓  
Signal  
↓  
Scenario  
↓  
Prediction  

Prediction must always depend on earlier layers.

Prediction must never bypass signals or scenarios.

---

# Principle 8  
Documentation Is Part of the Architecture

GenesisPrediction documentation is not optional.

Important architectural documents include:

docs/architecture/pipeline_overview.md  
docs/architecture/system_map.md  
docs/ui/ui_pages_reference.md  

These documents explain the system structure.

Future modifications must update documentation when necessary.

---

# Principle 9  
Complete Files Instead of Partial Patches

When generating or modifying code, the system follows a strict rule:

Always produce **complete files**.

Partial patches, fragmented edits, or ambiguous modifications must be avoided.

This rule prevents corruption caused by manual editing errors.

---

# Principle 10  
AI Must Respect the Architecture

GenesisPrediction may be developed with assistance from AI systems.

However, AI must respect the architectural rules defined in this document.

If an AI proposes modifications that violate these rules, the proposal must be rejected.

Examples of unacceptable AI behavior:

moving computation into the UI  
duplicating analysis logic in multiple locations  
breaking artifact contracts  
bypassing pipeline layers

These actions introduce architectural drift.

---

# Final Note

Complex systems decay when their original principles are forgotten.

GenesisPrediction was designed with clear separation of responsibilities, deterministic pipelines, and stable artifacts.

These rules exist so the system can grow without losing its structure.

The goal is not rigidity for its own sake.

The goal is **clarity, stability, and truthfulness of analysis**.

Future maintainers should preserve these principles.

Not because the system is sacred,

but because clear architecture protects understanding.
```
