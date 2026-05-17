# Decision Index (GenesisPrediction v2)

Status: Active
Purpose: Lightweight navigation for decision_log.md
Last Updated: 2026-05-17

---

# 0. Purpose

This file is navigation only.

```text
decision_index is not authority
decision_log.md is authority
archive is rationale only
```

---

# 1. Rules

- 1 decision = 1 entry
- Each entry contains title, tags, rule, source
- No long rationale
- Source must point to decision_log.md or archive when explicitly historical

---

# 2. Index Entries

## Core Authority / Governance

### CORE-001 | Decision Log Role Is Authoritative Operational Record
tags: decision_log, authority, archive
rule: decision_log.md records current binding decisions only; rationale and operational narratives live in docs/archive/decision_rationale/.
source: docs/core/decision_log.md

### CORE-002 | Decision Index Is Navigation Only
tags: decision_index, navigation
rule: decision_index.md is a lightweight search aid; it is not authority.
source: docs/core/decision_log.md

### CORE-003 | Rationale Archive Is Historical, Not Authority
tags: archive, rationale, authority
rule: docs/archive/decision_rationale preserves long-form reasoning but does not override decision_log.md.
source: docs/core/decision_log.md

### CORE-004 | Analysis Is Single Source of Truth
tags: analysis, ssot, architecture
rule: analysis/ is runtime truth; UI, vector memory, deploy snapshots, and archive must not override it.
source: docs/core/decision_log.md

### CORE-005 | Docs Are Single Source of Design Intent
tags: docs, design_intent, architecture
rule: docs/ stores design intent; analysis/ remains runtime truth.
source: docs/core/decision_log.md

### CORE-006 | UI Is Display Only
tags: ui, display_only, architecture
rule: UI reads generated artifacts and displays them; it must not compute, decide, translate, generate fallback meaning, or redefine truth.
source: docs/core/decision_log.md

### CORE-007 | Full File Delivery Only
tags: generation, integrity, full_file
rule: Diff proposals and partial patches are prohibited; complete files are required.
source: docs/core/decision_log.md

### CORE-008 | Existing File Verification Required
tags: generation, verification, no_guessing
rule: Existing files must be inspected before generation; do not reconstruct from guesswork.
source: docs/core/decision_log.md

### CORE-009 | Download/ZIP Workflow Required For Long Files
tags: markdown, zip, integrity
rule: Long Markdown/code artifacts must be delivered as downloadable complete files or ZIP; browser manual copy-paste is prohibited.
source: docs/core/decision_log.md

### CORE-010 | Line Count Integrity Must Be Checked
tags: line_count, integrity
rule: Line counts must be checked before/after file replacement; large reductions require explicit rationale.
source: docs/core/decision_log.md

### CORE-011 | Incomplete Input Guard
tags: no_guessing, stop, escalate
rule: If required input is missing, stop or escalate rather than inventing a plausible file.
source: docs/core/decision_log.md

## Architecture

### ARCH-001 | Pipeline Structure Is Fixed
tags: pipeline, architecture
rule: GenesisPrediction follows Observation → Trend → Signal → Scenario → Prediction, with Explanation, Vector Memory, FX Decision, and History Snapshot as supporting layers.
source: docs/core/decision_log.md

### ARCH-002 | WorldDate Uses Local Date
tags: worlddate, morning_ritual
rule: WorldDate uses LOCAL DATE because raw news files are saved by local date.
source: docs/core/decision_log.md

### ARCH-003 | Vector Memory Is Reference Only
tags: vector_memory, qdrant, reference
rule: Qdrant/vector memory is searchable reference memory; it must never overwrite analysis or become authority.
source: docs/core/decision_log.md

### ARCH-004 | Memory Is Promoted, Not Raw
tags: memory, promotion
rule: Only decisions, rules, and durable insights are promoted; raw conversations, trials, and temporary logs are not authoritative memory.
source: docs/core/decision_log.md

### ARCH-005 | Decision Log Is Primary Memory Source
tags: memory, decision_log
rule: decision_log.md is the primary source for decision memory indexing.
source: docs/core/decision_log.md

### ARCH-006 | build_vector_memory.py Is Single Entrypoint
tags: vector_memory, scripts
rule: Vector memory rebuild uses build_vector_memory.py as the single rebuild entrypoint.
source: docs/core/decision_log.md

### ARCH-007 | Reference Memory Is Compacted For UI
tags: reference_memory, ui
rule: Reference memory passed to UI is compacted by analysis/scripts; UI must not compact raw memory.
source: docs/core/decision_log.md

## Language / i18n

### I18N-001 | Global i18n Architecture Is Analysis-Side
tags: i18n, analysis, ui
rule: Translation and *_i18n generation happen in scripts/analysis; UI only selects and displays.
source: docs/core/decision_log.md

### I18N-002 | Language State Is Centrally Managed
tags: lang, theme, central_state
rule: LANG state is centrally managed like theme; pages do not directly own language state.
source: docs/core/decision_log.md

### I18N-003 | UI Must Not Generate Language
tags: ui, i18n, language
rule: UI must not translate, supplement, fallback-generate, compress, or reinterpret language content.
source: docs/core/decision_log.md

### I18N-004 | Runtime Text Must Not Compete With Static i18n
tags: i18n, runtime_text
rule: A DOM node must have one text responsibility; static labels and runtime content must not overwrite each other.
source: docs/core/decision_log.md

### I18N-005 | Static Labels May Use Central Dictionary
tags: i18n, labels
rule: Static labels may use central dictionary; dynamic runtime text must come from analysis *_i18n fields.
source: docs/core/decision_log.md

### I18N-006 | Prediction Output Must Preserve Structure
tags: prediction, i18n, structure
rule: Prediction output must not use partial word-level translation fallback; unknown phrases remain raw unless explicitly mapped.
source: docs/core/decision_log.md

### I18N-007 | Scenario Labels Must Not Use Generic Translation
tags: scenario, i18n, labels
rule: Scenario labels must be explicit canonical labels, not generic translation artifacts.
source: docs/core/decision_log.md

### I18N-008 | EN Is Internal SSOT For Language Architecture
tags: i18n, en, ssot
rule: English is the primary internal basis for generated i18n/artifacts; Japanese and Thai are supplementary display layers.
source: docs/core/decision_log.md

## Prediction / Scenario

### PRED-001 | Prediction Must Be Last Layer
tags: prediction, architecture
rule: Prediction is the final decision-grade summary; it must not replace Observation/Trend/Signal/Scenario.
source: docs/core/decision_log.md

### PRED-002 | Scenario Engine Must Produce Causal Branches
tags: scenario, causal, branch
rule: Scenario output must be causal, branch-readable, and monitoring-linked, not template text.
source: docs/core/decision_log.md

### PRED-003 | Scenario Drivers Must Be Cause-Oriented
tags: scenario, drivers, cause
rule: Scenario key_drivers must contain causes, not outcomes, state labels, or scenario names.
source: docs/core/decision_log.md

### PRED-004 | Prediction Must Be Decision-Grade
tags: prediction, decision_grade
rule: Prediction must be a decision-grade conclusion, not a scenario restatement.
source: docs/core/decision_log.md

### PRED-005 | Prediction Drivers Are Limited And Cause-Oriented
tags: prediction, drivers, cause
rule: Prediction key_drivers should be short, limited, and cause-oriented.
source: docs/core/decision_log.md

### PRED-006 | Monitoring Priorities Follow Branch Logic
tags: prediction, monitoring, branch_logic
rule: Monitoring priorities must preserve decision flow and branch logic, especially escalation and persistence before stabilization.
source: docs/core/decision_log.md

### PRED-007 | Scenario Driver Canonicalization Excludes Scenario Labels
tags: scenario, canonicalization
rule: Scenario labels such as base_case/best_case/worst_case must not enter driver canonicalization.
source: docs/core/decision_log.md

### PRED-008 | Scenario Transmission Is Deterministic Per Branch
tags: scenario, transmission
rule: Scenario transmission chains must be deterministic and branch-specific.
source: docs/core/decision_log.md

### PRED-009 | Scenario Narrative Uses Structured Drivers
tags: scenario, narrative
rule: Scenario narrative must be built from structured drivers, not raw tags.
source: docs/core/decision_log.md

### PRED-010 | Scenario Narrative Outcomes Align With Branch Outcomes
tags: scenario, outcomes
rule: Scenario narrative outcomes must align with branch expected outcomes.
source: docs/core/decision_log.md

### PRED-011 | Internal Scenario Tokens Are Snake Case
tags: scenario, tokens, snake_case
rule: Internal scenario/transmission tokens must use snake_case.
source: docs/core/decision_log.md

### PRED-012 | Scenario Carries Invalidation Conditions
tags: scenario, invalidation
rule: Scenario branches must carry invalidation conditions.
source: docs/core/decision_log.md

### PRED-013 | Scenario Engine Final Polish Is Baseline
tags: scenario, milestone
rule: The production-ready scenario baseline is causal branches + deterministic transmission + aligned narrative + snake_case tokens + invalidation.
source: docs/core/decision_log.md

## Explanation

### EXPL-001 | Explanation Is Mirror Of Prediction
tags: explanation, prediction, mirror
rule: Explanation mirrors prediction and must not reinterpret it or create new truth.
source: docs/core/decision_log.md

### EXPL-002 | Watchpoints Must Not Mix Layers
tags: watchpoints, explanation, prediction
rule: Prediction monitoring_priorities take precedence; explanation must not mix scenario/signal watchpoints when prediction watchpoints exist.
source: docs/core/decision_log.md

### EXPL-003 | Explanation Fields Mirror Prediction Fields
tags: explanation, mirror, structure
rule: drivers, monitoring, implications, risks, and invalidation must mirror prediction fields directly.
source: docs/core/decision_log.md

### EXPL-004 | Explanation May Clarify Reading Only
tags: explanation, no_new_truth
rule: Explanation may structure reading guidance and misread prevention, but must not add new causes, risks, or watchpoints.
source: docs/core/decision_log.md

### EXPL-005 | Explanation Drivers Are Pure Prediction Mirror
tags: explanation, drivers, mirror
rule: explanation.drivers mirror prediction.key_drivers / prediction.drivers without extra why/impact reconstruction.
source: docs/core/decision_log.md

### EXPL-006 | Explanation Core Fields Are Pure Prediction Mirror
tags: explanation, core_fields, mirror
rule: Explanation core fields mirror prediction directly without structured reinterpretation.
source: docs/core/decision_log.md

## Operations / Deploy

### OPS-001 | Deploy Target Is Snapshot
tags: deploy, labos, snapshot
rule: LABOS is a distribution snapshot; Git + analysis/data remain authoritative.
source: docs/core/decision_log.md

### OPS-002 | Deploy Is Full Replacement
tags: deploy, full_replacement
rule: Deploy must fully replace target state and must not overlay stale files.
source: docs/core/decision_log.md

### OPS-003 | Deploy Must Be Target-Isolated
tags: deploy, conoha, safety
rule: Deploy must only operate inside the intended LABOS target and must not affect other hosted sites.
source: docs/core/decision_log.md

### OPS-004 | Deploy Payload Self-Deletion Guard
tags: deploy, payload, guard
rule: Cleanup logic must not delete the deploy payload before extraction.
source: docs/core/decision_log.md

### OPS-005 | Deploy Verification Must Follow Deploy
tags: deploy, verify
rule: Deploy success is not final; verify_deploy.py/local-vs-public comparison must pass.
source: docs/core/decision_log.md

### OPS-006 | Morning Ritual Chain Is Formal
tags: morning_ritual, deploy, verify
rule: Morning Ritual → post checks → deploy → verify is the formal end-to-end operational chain.
source: docs/core/decision_log.md

### OPS-007 | Build And View Environments Are Separated
tags: environment, build, view
rule: Home/build PC generates analysis/data; company/view PC consumes and verifies only.
source: docs/core/decision_log.md

### OPS-008 | Company PC Must Not Regenerate Analysis/Data
tags: environment, no_build
rule: Company PC must not run Morning Ritual or regenerate analysis/data.
source: docs/core/decision_log.md

### OPS-009 | analysis/data USB Sync Is Valid Transport
tags: sync, transport
rule: Whole analysis/data sync from build environment to view environment is valid; do not regenerate on view side.
source: docs/core/decision_log.md

### OPS-010 | Git Restore Is Destructive Rollback
tags: git, restore, rollback
rule: git restore is destructive rollback and must only be used after explicit rollback decision.
source: docs/core/decision_log.md

### OPS-011 | Detached HEAD Work Is Not Trusted Final State
tags: git, detached_head
rule: Detached HEAD work is not final until returned to main and committed/stashed intentionally.
source: docs/core/decision_log.md

### OPS-012 | Local Cache Failure Is Operational Incident
tags: cache, fastembed, incident
rule: fastembed/local cache failures are operational incidents, not architecture failures.
source: docs/core/decision_log.md

### OPS-013 | Automation Must Expose Phase Status And Exit Code
tags: automation, status, exit_code
rule: Unattended automation must expose per-phase OK/FAIL/SKIP and unified final exit code.
source: docs/core/decision_log.md

### OPS-014 | Vector Rebuild Self-Healing Is Valid
tags: vector_memory, self_healing
rule: WARN → rebuild → re-check → OK for vector freshness is valid self-healing behavior.
source: docs/core/decision_log.md

### OPS-015 | Dirty Repo Guard Enforced
tags: git, dirty_guard
rule: Run scripts must execute on a clean working tree.
source: docs/core/decision_log.md

### OPS-016 | Pre-Run Commit Required
tags: git, commit, operations
rule: Commit before run is mandatory to satisfy dirty guard and preserve reproducibility.
source: docs/core/decision_log.md

### OPS-017 | PowerShell Switch Parameters Do Not Receive Boolean Values
tags: powershell, switch
rule: PowerShell switch parameters are enabled by presence and must not receive explicit boolean values.
source: docs/core/decision_log.md

### OPS-018 | Cross-Platform PowerShell Prefers pwsh On Core
tags: powershell, github_actions
rule: PowerShell Core environments must dynamically resolve pwsh instead of powershell.
source: docs/core/decision_log.md

### OPS-019 | NoLLM Morning Ritual GitHub Actions Trial Succeeded
tags: github_actions, nollm, labos
rule: NoLLM GitHub Actions workflow can support iPad-driven LABOS updates when SSH restrictions are resolved.
source: docs/core/decision_log.md

### OPS-020 | Deploy Verify Is Technical, Not Semantic Truth
tags: deploy, verify, semantic_integrity
rule: verify_deploy.py confirms deployed artifacts match local artifacts; it does not prove that generated meaning, dates, or pipeline logic are correct.
source: docs/core/decision_log.md

## Data / Analysis

### DATA-001 | Sentiment Output Is Semantic
tags: sentiment, semantic
rule: Sentiment output includes theme_tags, signal_tags, risk_drivers, and impact_tags for Prediction/Scenario use.
source: docs/core/decision_log.md

### DATA-002 | World View Summary Is Structured First
tags: world_view, summary
rule: World view summary derives from structured summary, not malformed upstream free text.
source: docs/core/decision_log.md

### DATA-003 | Prediction Uses Semantic Analysis Fields
tags: prediction, semantic
rule: Prediction consumes semantic analysis fields, not score-only sentiment.
source: docs/core/decision_log.md

### DATA-004 | Daily Summary Is Count-Based
tags: summary, count
rule: daily_summary_latest summary must be derived from count-based structured fields and not contradict today.count.
source: docs/core/decision_log.md

### DATA-005 | Health Output Path Matches SSOT Path
tags: health, ssot, path
rule: build_data_health.py output must align with analysis/health_latest.json when guards verify that path.
source: docs/core/decision_log.md

### DATA-006 | World Latest Pointer Must Sync During News Publish
tags: world_politics, latest_pointer, as_of, publish
rule: Publishing daily world news must synchronize data/world_politics/analysis/latest.json with the dated raw source so downstream view/global status artifacts do not drift to stale as_of dates.
source: docs/core/decision_log.md

### DATA-007 | Dated Raw Source Is Authority Over latest.json
tags: world_politics, authority, latest_pointer, stale_prevention
rule: When a dated raw world news source exists for the requested/local date, pipeline truth selection must prefer the dated source over analysis/latest.json to prevent stale as_of drift.
source: docs/core/decision_log.md

## UI / Public Release

### UI-001 | UI Must Not Silently Mask Missing Data
tags: ui, missing_data, silent_failure
rule: Missing data must be visible as loading/missing/unavailable, not hidden as normal output.
source: docs/core/decision_log.md

### UI-002 | Release Requires Analysis Completeness
tags: release, analysis, completeness
rule: Deploy/release requires necessary latest JSON and *_i18n keys; UI fixes must not cover incomplete analysis.
source: docs/core/decision_log.md

### UI-003 | Digest Summary i18n Generated In Analysis
tags: digest, i18n
rule: Digest summary_i18n is generated in analysis and displayed by UI only.
source: docs/core/decision_log.md

### UI-004 | Prediction History Syncs To Data Layer For UI
tags: history, data_layer, ui
rule: Prediction history must be synced to data layer paths needed by the UI distribution.
source: docs/core/decision_log.md

### UI-005 | Local Server And Distribution Are Distinct
tags: distribution, local_server
rule: Local dev server structure and dist/deploy structure must not be confused.
source: docs/core/decision_log.md

### UI-006 | UI 404 Debug Starts From Distribution Layer
tags: ui, debug, distribution
rule: UI 404 issues must be debugged from distribution/build output before page logic.
source: docs/core/decision_log.md

### UI-007 | GUI Final Audit Completed
tags: ui, audit
rule: GUI final audit established the public UI baseline.
source: docs/core/decision_log.md

### UI-008 | Pre-Deploy Payload Freshness Check Required
tags: deploy, payload, freshness
rule: Deploy payload must be checked for freshness before deployment.
source: docs/core/decision_log.md

### UI-009 | Favicon And OGP Handling In Static Deployment
tags: seo, ogp, favicon
rule: Static deploy must preserve favicon and OGP asset paths.
source: docs/core/decision_log.md

### UI-010 | Home Is Route-First Public Landing Page
tags: home, landing, public
rule: Home must guide users to Digest, Overlay, and Prediction as route-first public landing page.
source: docs/core/decision_log.md

### UI-011 | Prediction Static Text Resolves Locally
tags: prediction, ui_text, i18n
rule: Prediction page static labels resolve from page-local UI_TEXT when required, not conflicting shared runtime routing.
source: docs/core/decision_log.md

## Policy / Public Content

### POLICY-001 | News Content Must Not Be Reproduced In Full
tags: news, copyright, policy
rule: GenesisPrediction summarizes and links news; it must never reproduce full articles or large source text.
source: docs/core/decision_log.md

### POLICY-002 | Policy Docs Are Human-Facing; AI Rules Are Compressed
tags: policy, decision_log
rule: Detailed policy docs may exist for humans, but AI-effective rules must be compressed into decision_log and indexed.
source: docs/core/decision_log.md

## Thread Governance

### THREAD-001 | Thread Objective Freeze And Completion Boundary
tags: thread, scope, completion
rule: Each thread must freeze objective and completion boundary to avoid infinite expansion.
source: docs/core/decision_log.md

### CORE-012 | Archive Rationale Map Required
tags: archive, consolidation, map
rule: decision_log consolidation must include a map that explains where legacy rationale moved and how authority was preserved.
source: docs/core/decision_log.md

### CORE-013 | Consolidation Report Required
tags: archive, consolidation, report
rule: decision_log consolidation must include a report documenting line counts, reduction rationale, archive coverage, and vector indexing intent.
source: docs/core/decision_log.md

### CORE-014 | Legacy Decision Log Must Be Preserved
tags: archive, legacy, integrity
rule: the pre-consolidation decision_log must be preserved in rationale archive before compact authority replacement is accepted.
source: docs/core/decision_log.md

### ARCH-008 | VectorDB Must Separate Authority And Rationale Memory
tags: vector_memory, authority, rationale
rule: decision_log entries and archive rationale must be indexed as separate reference memory types and must not be treated as equal authority.
source: docs/core/decision_log.md

### ARCH-009 | Archive Recall Is Context Only
tags: vector_memory, archive, recall
rule: archive recall may explain history and rationale but must not override current decision_log authority.
source: docs/core/decision_log.md

### ARCH-010 | Downstream Layers Must Not Feed Upstream
tags: pipeline, dependency, feedback_loop
rule: Later pipeline layers must not be read by earlier layers; Prediction must not feed Trend/Signal/Scenario or create feedback loops.
source: docs/core/decision_log.md

---

END OF DOCUMENT
