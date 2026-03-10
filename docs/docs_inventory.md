# Docs Inventory

GenesisPrediction v2

Purpose
- Define the documentation structure of the repository
- Clarify the role of each docs folder
- Prevent new documents from being placed inconsistently
- Make it easy for future AI instances and developers to understand where each file belongs

This document is the official inventory and classification guide for `docs/`.

---

# Basic Policy

GenesisPrediction uses a structured documentation model.

Main categories:

```text
docs/core
docs/active
docs/reference
docs/runbook
docs/ADR
docs/archive
docs/obsolete
````

The goal is:

* keep current architecture easy to find
* separate active design from reference material
* preserve historical records without polluting active docs
* reduce confusion for future maintenance

---

# Folder Roles

## docs/core

Role

Core documents that define the long-term identity and structural foundation of GenesisPrediction.

Use this folder for:

* system-wide principles
* long-term architecture anchors
* project-wide status and history
* foundational design rules
* core UI philosophy and standards

Examples already present:

```text
docs/core/decision_log.md
docs/core/genesis_brain.md
docs/core/GenesisPrediction_UI_Work_Rules.md
docs/core/prediction_layer_design_principles.md
docs/core/project_status.md
docs/core/system_history.md
docs/core/ui/docs_architecture.md
docs/core/ui/global_status_component_standard.md
docs/core/ui/global_status_css_standard.md
docs/core/ui/global_status_data_mapping.md
docs/core/ui/global_status_html_standard.md
docs/core/ui/ui_component_catalog.md
docs/core/ui/ui_design_philosophy.md
docs/core/ui/ui_index.md
docs/core/ui/ui_layout_standard.md
```

Core documents should be stable and few.

---

## docs/active

Role

Current active system design and implementation-target documents.

Use this folder for:

* current architecture
* active layer design
* current data schema
* pipeline design
* current engine design
* system maps in active use

Examples already present:

```text
docs/active/analysis_data_schema.md
docs/active/genesis_prediction_roadmap.md
docs/active/genesis_system_map.md
docs/active/pipeline_system.md
docs/active/prediction_architecture.md
docs/active/repo_map.md
docs/active/ui_data_dependencies.md
docs/active/ui_system.md
```

Prediction and Observation documents that define the current working architecture belong here.

---

## docs/reference

Role

Reference material for AI operation, repository memory, supporting rules, helper documents, and supporting context.

Use this folder for:

* AI bootstrap references
* AI operating notes
* supporting rules
* helper documentation
* checklists that are not primary architecture
* contextual documents useful for lookup

Examples already present:

```text
docs/reference/ai_bootstrap.md
docs/reference/ai_quick_context.md
docs/reference/ai_rules.md
docs/reference/chat_operating_rules.md
docs/reference/debug_playbook.md
docs/reference/repository_memory_index.md
docs/reference/working_agreement.md
```

Reference docs support the system, but do not define the active architecture itself.

---

## docs/runbook

Role

Operational procedures and execution guides.

Use this folder for:

* daily operational instructions
* environment-specific run procedures
* company PC procedures
* Morning Ritual execution procedures
* operator cheat sheets
* repeatable human workflows

Examples already present:

```text
docs/runbook/company_pc_verification_cheatsheet.md
docs/runbook/daily_routine_v1.md
docs/runbook/openwebui_prompt_templates.md
```

Any doc whose primary purpose is "how to run or operate something" belongs here.

---

## docs/ADR

Role

Architectural Decision Records.

Use this folder for:

* important architecture decisions
* repository policy decisions
* design rationale that should be preserved as decisions

Examples already present:

```text
docs/ADR/0001-repository-memory.md
docs/ADR/0002-analysis-as-sst.md
docs/ADR/README.md
```

ADR files should remain small, explicit, and decision-oriented.

---

## docs/archive

Role

Historical records and old materials kept for reference.

Use this folder for:

* old specs
* snapshots
* retired but historically useful documents
* prior generation documents that may still be referenced

Examples already present:

```text
docs/archive/sentiment_server_snapshot_2026-03.html
docs/archive/constitution/file_generation_rules_v1.md
docs/archive/specs/fx_operation_spec_v1.md
docs/archive/specs/sentiment_spec_v1.md
```

Archive is not for active design.

Archive is for preservation.

---

## docs/obsolete

Role

Documents no longer in active or reference use.

Use this folder for:

* deprecated contracts
* documents replaced by better versions
* legacy categories that should not be used anymore

Examples already present:

```text
docs/obsolete/contracts/README.md
```

Obsolete means the document should generally not be used in current design decisions.

---

# Root-Level Rule

The `docs/` root should stay minimal.

Allowed at root:

* top-level index and entry documents
* temporary documents awaiting classification
* only truly cross-category files

Preferred permanent root files:

```text
docs/README.md
docs/INDEX.md
docs/docs_inventory.md
```

Everything else should preferably live inside one of the structured folders.

---

# Recommended Classification for Current Root Files

The following files should remain or be moved according to the policy below.

---

## Keep at root

These may remain at root because they serve as top-level entry points.

```text
docs/README.md
docs/INDEX.md
docs/docs_inventory.md
```

Role split:

* `README.md` = entry point to docs
* `INDEX.md` = document index / quick map
* `docs_inventory.md` = folder policy and classification rules

---

## Move to docs/active

These are active design and architecture documents.

```text
docs/early_warning_engine_design.md
docs/observation.md
docs/prediction_data_schema.md
docs/prediction_engine.md
docs/prediction_history.md
docs/prediction_history_ui.md
docs/prediction_layer_design.md
docs/prediction_pipeline_design.md
docs/prediction_runtime.md
docs/prediction_system_overview.md
docs/scenario_engine.md
docs/scenario_layer_design.md
docs/signal_engine.md
docs/signal_layer_design.md
docs/trend_engine.md
docs/trend_layer_design.md
```

These define the current Prediction / Observation system and should be grouped with other active system docs.

---

## Move to docs/reference

These are support, AI, helper, checklist, or contextual materials.

```text
docs/ai_bootstrap_prompt.md
docs/ai_knowledge_sources.md
docs/ai_memory_architecture.md
docs/AI_PROJECT_BOOTSTRAP.md
docs/AI_SELF_BOOT_PROMPT.md
docs/ai_startup_protocol.md
docs/ai_thread_start_template.md
docs/assumptions.md
docs/data_sync_rule.md
docs/diff_schema.md
docs/fragile_points.md
docs/fx_remittance_recommend_handover.md
docs/genesis_docs_map.md
docs/gui_commercial_checklist.md
docs/gui_f1_panel_spec.md
docs/gui_phase2_working_rules.md
docs/labos_business_model.md
docs/memory_layer_complete_architecture.md
docs/memory_layer_morning_ritual_integration.md
docs/overlay_image_design.md
docs/README_fx_monthly_report_gui.md
docs/task_board.md
docs/thread_templates.md
docs/TODO_syncthing_setup.md
docs/ui_final_checklist.md
```

These are important, but they are not the main active architecture spine.

---

## Move to docs/runbook

These are operational procedures.

```text
docs/ops_runbook.md
docs/runbook.md
docs/runbook_morning.md
docs/runbook_openwebui_company_pc.md
```

Their primary purpose is operation, so they belong under runbook.

---

## Review before moving to docs/core

These are strong candidates for core, but should be reviewed carefully to avoid making core too large.

```text
docs/genesis_complete_architecture.md
docs/repo_architecture.md
```

Recommended rule:

* if the document defines long-term project structure, move to `docs/core/`
* if it mainly describes current implementation architecture, move to `docs/active/`

Default recommendation:

```text
docs/genesis_complete_architecture.md -> docs/core/
docs/repo_architecture.md -> docs/core/
```

---

# Folder Usage Rules for New Documents

When adding new docs, apply the following rule.

## Put in docs/core when

* the file defines long-term project identity
* the file describes permanent design principles
* the file is foundational across many layers
* the file should be consulted for months or years

## Put in docs/active when

* the file defines the current architecture
* the file guides the current implementation phase
* the file defines active runtime behavior
* the file describes current layer design or schema

## Put in docs/reference when

* the file supports AI operation
* the file is a helper guide or context reference
* the file is informative but not the system spine
* the file is lookup material

## Put in docs/runbook when

* the file tells a human how to operate a workflow
* the file is a routine checklist
* the file is machine or environment operation guidance

## Put in docs/archive when

* the file is old but worth preserving
* the file belongs to a previous generation
* the file is a historical snapshot

## Put in docs/obsolete when

* the file is no longer useful for current operation
* the file is superseded
* the file should be preserved only to avoid accidental reuse

---

# Current High-Level Inventory

As of the current organization, `docs/` consists of these major groups.

## Top level folders

```text
docs/active
docs/ADR
docs/archive
docs/core
docs/obsolete
docs/reference
docs/runbook
```

## Existing active system spine

```text
docs/active/analysis_data_schema.md
docs/active/genesis_prediction_roadmap.md
docs/active/genesis_system_map.md
docs/active/pipeline_system.md
docs/active/prediction_architecture.md
docs/active/repo_map.md
docs/active/ui_data_dependencies.md
docs/active/ui_system.md
```

## Existing core spine

```text
docs/core/decision_log.md
docs/core/genesis_brain.md
docs/core/GenesisPrediction_UI_Work_Rules.md
docs/core/prediction_layer_design_principles.md
docs/core/project_status.md
docs/core/system_history.md
```

## Existing UI core spine

```text
docs/core/ui/docs_architecture.md
docs/core/ui/global_status_component_standard.md
docs/core/ui/global_status_css_standard.md
docs/core/ui/global_status_data_mapping.md
docs/core/ui/global_status_html_standard.md
docs/core/ui/ui_component_catalog.md
docs/core/ui/ui_design_philosophy.md
docs/core/ui/ui_index.md
docs/core/ui/ui_layout_standard.md
```

## Existing reference spine

```text
docs/reference/ai_bootstrap.md
docs/reference/ai_quick_context.md
docs/reference/ai_rules.md
docs/reference/chat_operating_rules.md
docs/reference/debug_playbook.md
docs/reference/repository_memory_index.md
docs/reference/working_agreement.md
```

---

# Immediate Cleanup Priority

Recommended cleanup order:

## Phase 1

Move active design files from `docs/` root into `docs/active/`

## Phase 2

Move run procedures from `docs/` root into `docs/runbook/`

## Phase 3

Move AI and support docs from `docs/` root into `docs/reference/`

## Phase 4

Review architecture root docs for `docs/core/` or `docs/active/`

## Phase 5

Update `docs/README.md` and `docs/INDEX.md` to reflect the final structure

---

# Practical Principle

The docs tree should answer these questions instantly.

* What defines the system?
* What is active right now?
* What is reference only?
* What do I run?
* What is historical?
* What should not be used anymore?

If the tree answers those clearly, the documentation system is healthy.

---

# Summary

GenesisPrediction documentation structure is:

```text
docs/core       = long-term core architecture and principles
docs/active     = current active system design
docs/reference  = supporting reference and AI context
docs/runbook    = operational procedures
docs/ADR        = architectural decision records
docs/archive    = historical preserved materials
docs/obsolete   = deprecated materials
```

Root-level `docs/` should remain minimal.

Preferred permanent root files:

```text
docs/README.md
docs/INDEX.md
docs/docs_inventory.md
```

All other documents should be classified into the correct folder whenever possible.

This file is the official guide for future docs organization.

```
