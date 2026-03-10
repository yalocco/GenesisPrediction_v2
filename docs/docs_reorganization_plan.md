# Docs Reorganization Plan

GenesisPrediction v2

Purpose
- Define the practical cleanup plan for the `docs/` directory
- Convert the inventory policy into actual move steps
- Reduce confusion caused by root-level document sprawl
- Make future maintenance easier for both humans and AI instances

This document is the execution plan for reorganizing `docs/`.

It follows the folder policy defined in:

```text
docs/docs_inventory.md
````

---

# Reorganization Goal

The goal is simple.

Keep `docs/` root minimal.

Move most files into one of these structured folders:

```text
docs/core
docs/active
docs/reference
docs/runbook
docs/ADR
docs/archive
docs/obsolete
```

Desired outcome:

* current architecture is easy to find
* current implementation docs are grouped together
* run procedures are separate from design docs
* AI reference material is separate from active architecture
* historical material stays preserved but out of the active path

---

# Reorganization Principles

## Principle 1

Do not move files blindly.

Classification must follow folder role.

## Principle 2

Move active architecture first.

These have the highest day-to-day value.

## Principle 3

Keep root-level entry files minimal and stable.

## Principle 4

Do not delete historical material during reorganization.

If unsure, prefer move to `archive/` rather than deletion.

## Principle 5

After moves are complete, update index files.

Especially:

```text
docs/README.md
docs/INDEX.md
```

---

# Target End State

Preferred permanent root files:

```text
docs/README.md
docs/INDEX.md
docs/docs_inventory.md
docs/docs_reorganization_plan.md
```

Optional temporary root files may exist briefly during transition, but should not remain permanently.

---

# Reorganization Phases

## Phase 1 — Move active architecture documents

These files define the current working Observation / Trend / Signal / Scenario / Prediction architecture.

Move from root to:

```text
docs/active/
```

Target files:

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

Reason:

These are active system design and implementation-target documents.

This is the highest priority move.

---

## Phase 2 — Move operational procedures

These files are operational guides and run procedures.

Move from root to:

```text
docs/runbook/
```

Target files:

```text
docs/ops_runbook.md
docs/runbook.md
docs/runbook_morning.md
docs/runbook_openwebui_company_pc.md
```

Reason:

Their primary purpose is operational guidance, not architecture.

---

## Phase 3 — Move AI/support/reference documents

These are supporting context, AI workflow materials, helper documents, and secondary reference materials.

Move from root to:

```text
docs/reference/
```

Target files:

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

Reason:

These are important, but not part of the main active architecture spine.

---

## Phase 4 — Review long-term architecture anchors

These files need deliberate review before moving.

Candidates:

```text
docs/genesis_complete_architecture.md
docs/repo_architecture.md
```

Recommended destination:

```text
docs/core/
```

Decision rule:

* if the file defines long-term structural identity, move to `docs/core/`
* if the file mostly documents current implementation, move to `docs/active/`

Default recommendation:

```text
docs/genesis_complete_architecture.md -> docs/core/
docs/repo_architecture.md -> docs/core/
```

---

## Phase 5 — Keep top-level entry files at root

These should remain in `docs/` root:

```text
docs/README.md
docs/INDEX.md
docs/docs_inventory.md
docs/docs_reorganization_plan.md
```

Reason:

These act as the documentation entry layer.

---

## Phase 6 — Validate category health

After moving files, check that:

* `docs/active/` contains only current architecture and active implementation docs
* `docs/reference/` contains support and lookup material
* `docs/runbook/` contains operator procedures
* `docs/core/` remains small and foundational
* `docs/archive/` remains historical
* `docs/obsolete/` remains deprecated-only

This is a review phase, not a move phase.

---

## Phase 7 — Update indexes

After the move is complete, update:

```text
docs/README.md
docs/INDEX.md
```

These should reflect the new structure clearly.

Possible updates:

* folder overview
* major active docs list
* core architecture entry points
* runbook entry points
* reference entry points

---

# Recommended Execution Order

Safe execution order:

```text
1 Move active files
2 Move runbook files
3 Move reference files
4 Review core candidates
5 Update README and INDEX
6 Final repo verification
```

This order minimizes confusion during the transition.

---

# Suggested Move Map

## Root -> docs/active

```text
docs/early_warning_engine_design.md      -> docs/active/early_warning_engine_design.md
docs/observation.md                      -> docs/active/observation.md
docs/prediction_data_schema.md           -> docs/active/prediction_data_schema.md
docs/prediction_engine.md                -> docs/active/prediction_engine.md
docs/prediction_history.md               -> docs/active/prediction_history.md
docs/prediction_history_ui.md            -> docs/active/prediction_history_ui.md
docs/prediction_layer_design.md          -> docs/active/prediction_layer_design.md
docs/prediction_pipeline_design.md       -> docs/active/prediction_pipeline_design.md
docs/prediction_runtime.md               -> docs/active/prediction_runtime.md
docs/prediction_system_overview.md       -> docs/active/prediction_system_overview.md
docs/scenario_engine.md                  -> docs/active/scenario_engine.md
docs/scenario_layer_design.md            -> docs/active/scenario_layer_design.md
docs/signal_engine.md                    -> docs/active/signal_engine.md
docs/signal_layer_design.md              -> docs/active/signal_layer_design.md
docs/trend_engine.md                     -> docs/active/trend_engine.md
docs/trend_layer_design.md               -> docs/active/trend_layer_design.md
```

## Root -> docs/runbook

```text
docs/ops_runbook.md                      -> docs/runbook/ops_runbook.md
docs/runbook.md                          -> docs/runbook/runbook.md
docs/runbook_morning.md                  -> docs/runbook/runbook_morning.md
docs/runbook_openwebui_company_pc.md     -> docs/runbook/runbook_openwebui_company_pc.md
```

## Root -> docs/reference

```text
docs/ai_bootstrap_prompt.md              -> docs/reference/ai_bootstrap_prompt.md
docs/ai_knowledge_sources.md             -> docs/reference/ai_knowledge_sources.md
docs/ai_memory_architecture.md           -> docs/reference/ai_memory_architecture.md
docs/AI_PROJECT_BOOTSTRAP.md             -> docs/reference/AI_PROJECT_BOOTSTRAP.md
docs/AI_SELF_BOOT_PROMPT.md              -> docs/reference/AI_SELF_BOOT_PROMPT.md
docs/ai_startup_protocol.md              -> docs/reference/ai_startup_protocol.md
docs/ai_thread_start_template.md         -> docs/reference/ai_thread_start_template.md
docs/assumptions.md                      -> docs/reference/assumptions.md
docs/data_sync_rule.md                   -> docs/reference/data_sync_rule.md
docs/diff_schema.md                      -> docs/reference/diff_schema.md
docs/fragile_points.md                   -> docs/reference/fragile_points.md
docs/fx_remittance_recommend_handover.md -> docs/reference/fx_remittance_recommend_handover.md
docs/genesis_docs_map.md                 -> docs/reference/genesis_docs_map.md
docs/gui_commercial_checklist.md         -> docs/reference/gui_commercial_checklist.md
docs/gui_f1_panel_spec.md                -> docs/reference/gui_f1_panel_spec.md
docs/gui_phase2_working_rules.md         -> docs/reference/gui_phase2_working_rules.md
docs/labos_business_model.md             -> docs/reference/labos_business_model.md
docs/memory_layer_complete_architecture.md -> docs/reference/memory_layer_complete_architecture.md
docs/memory_layer_morning_ritual_integration.md -> docs/reference/memory_layer_morning_ritual_integration.md
docs/overlay_image_design.md             -> docs/reference/overlay_image_design.md
docs/README_fx_monthly_report_gui.md     -> docs/reference/README_fx_monthly_report_gui.md
docs/task_board.md                       -> docs/reference/task_board.md
docs/thread_templates.md                 -> docs/reference/thread_templates.md
docs/TODO_syncthing_setup.md             -> docs/reference/TODO_syncthing_setup.md
docs/ui_final_checklist.md               -> docs/reference/ui_final_checklist.md
```

## Root -> docs/core (reviewed move)

```text
docs/genesis_complete_architecture.md    -> docs/core/genesis_complete_architecture.md
docs/repo_architecture.md                -> docs/core/repo_architecture.md
```

---

# Files Not To Move In This Phase

Do not move these during this plan.

```text
docs/README.md
docs/INDEX.md
docs/docs_inventory.md
docs/docs_reorganization_plan.md
docs/.stignore
```

Reason:

These are top-level meta files or utility files.

---

# Risks and Precautions

## Risk 1 — Broken internal links

Some files may reference paths such as:

```text
docs/prediction_runtime.md
```

After moving, those links may need updating to:

```text
docs/active/prediction_runtime.md
```

Mitigation:

After moves, run a path review across docs.

## Risk 2 — Duplicate meaning across folders

Some documents may overlap with already existing `docs/active/` files.

Examples to watch:

```text
docs/active/prediction_architecture.md
docs/prediction_system_overview.md
docs/genesis_complete_architecture.md
```

Mitigation:

Keep all during move phase. Consolidate only after structure becomes stable.

## Risk 3 — Overgrowing docs/core

Core must stay selective.

Mitigation:

Move only foundational documents into `core`.

## Risk 4 — README and INDEX becoming stale

Mitigation:

Update them after reorganization is complete.

---

# Verification Checklist

After the reorganization, verify:

* root-level clutter is reduced
* active prediction docs are together
* run procedures are together
* reference docs are together
* top-level entry docs remain usable
* no important file disappeared
* git status shows only intended moves
* internal path references are reviewed

---

# Suggested Git Strategy

Recommended working style:

## Step 1

Move active docs and commit

## Step 2

Move runbook docs and commit

## Step 3

Move reference docs and commit

## Step 4

Move reviewed core docs and commit

## Step 5

Update README and INDEX and commit

This creates a clean history and makes rollback easy.

Suggested commit style:

```text
Docs: move active architecture files into docs/active
Docs: move operational guides into docs/runbook
Docs: move AI and support materials into docs/reference
Docs: move core architecture anchors into docs/core
Docs: refresh README and INDEX after docs reorganization
```

---

# Practical Recommendation

Do not attempt all cleanup and content rewriting in one turn.

Best practice:

* move files first
* stabilize structure
* update indexes second
* resolve overlapping docs third

This keeps the transition safe.

---

# Summary

This reorganization plan defines how to convert the current mixed `docs/` root into a cleaner structure.

Primary actions:

```text
Move active architecture docs into docs/active
Move run procedures into docs/runbook
Move support and AI docs into docs/reference
Review architecture anchors for docs/core
Keep only entry/meta files at docs root
Update README and INDEX after moves
```

The result will be a documentation tree that is easier to read, safer to maintain, and far more understandable for future development.

This file is the official execution plan for docs cleanup.

```
