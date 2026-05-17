# Decision Log (GenesisPrediction v2)

Status: Active
Purpose: Authoritative operational decision record
Last Updated: 2026-05-17
Consolidation: authority/archive/vector hierarchy applied

---

# 0. Purpose

This document records current binding decisions for GenesisPrediction v2.

It is intentionally compact. Long-form rationale, operational narrative, and historical explanation are archived separately.

```text
decision_log.md = authoritative operational decision record
decision_index.md = navigation only
docs/archive/decision_rationale/ = historical rationale / explanation
VectorDB = reference memory only
```

Core principle:

```text
decision_log must remain readable enough to govern
```

---

# 1. Authority Hierarchy

```text
analysis/ = runtime truth
docs/core/decision_log.md = operational decision authority
docs/core/decision_index.md = navigation
docs/archive/decision_rationale/ = rationale archive
Qdrant / VectorDB = reference recall only
app/static/ = display only
LABOS = deploy snapshot
```

Rules:

- Archived rationale may explain a decision but must not override the compact decision record.
- Vector recall may assist work but must not become authority.
- UI must never become a decision, translation, fallback, or computation layer.
- Missing source files or insufficient input require STOP / ESCALATE, not guesswork.

---

# 2. Consolidation Decision

## 2026-05-09 | Decision Log Consolidation

Decision: Split authoritative decisions from historical rationale.

Rule:

```text
Current binding decisions stay in docs/core/decision_log.md.
Long-form reasoning moves to docs/archive/decision_rationale/.
decision_index.md remains navigation only.
VectorDB indexes source material as reference only.
```

Reason:

The previous decision_log grew into operational memory. That made it harder to read, govern, and use as an authority source. The archive preserves history while the decision_log stays compact.

Status: adopted

---

# 3. Decision Catalog

## Core Authority / Governance

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| CORE-001 | Decision Log Role Is Authoritative Operational Record | decision_log.md records current binding decisions only; rationale and operational narratives live in docs/archive/decision_rationale/. | decision_log, authority, archive |
| CORE-002 | Decision Index Is Navigation Only | decision_index.md is a lightweight search aid; it is not authority. | decision_index, navigation |
| CORE-003 | Rationale Archive Is Historical, Not Authority | docs/archive/decision_rationale preserves long-form reasoning but does not override decision_log.md. | archive, rationale, authority |
| CORE-004 | Analysis Is Single Source of Truth | analysis/ is runtime truth; UI, vector memory, deploy snapshots, and archive must not override it. | analysis, ssot, architecture |
| CORE-005 | Docs Are Single Source of Design Intent | docs/ stores design intent; analysis/ remains runtime truth. | docs, design_intent, architecture |
| CORE-006 | UI Is Display Only | UI reads generated artifacts and displays them; it must not compute, decide, translate, generate fallback meaning, or redefine truth. | ui, display_only, architecture |
| CORE-007 | Full File Delivery Only | Diff proposals and partial patches are prohibited; complete files are required. | generation, integrity, full_file |
| CORE-008 | Existing File Verification Required | Existing files must be inspected before generation; do not reconstruct from guesswork. | generation, verification, no_guessing |
| CORE-009 | Download/ZIP Workflow Required For Long Files | Long Markdown/code artifacts must be delivered as downloadable complete files or ZIP; browser manual copy-paste is prohibited. | markdown, zip, integrity |
| CORE-010 | Line Count Integrity Must Be Checked | Line counts must be checked before/after file replacement; large reductions require explicit rationale. | line_count, integrity |
| CORE-011 | Incomplete Input Guard | If required input is missing, stop or escalate rather than inventing a plausible file. | no_guessing, stop, escalate |
| CORE-012 | Archive Rationale Map Required | decision_log consolidation must include a map that explains where legacy rationale moved and how authority was preserved. | archive, consolidation, map |
| CORE-013 | Consolidation Report Required | decision_log consolidation must include a report documenting line counts, reduction rationale, archive coverage, and vector indexing intent. | archive, consolidation, report |
| CORE-014 | Legacy Decision Log Must Be Preserved | the pre-consolidation decision_log must be preserved in rationale archive before compact authority replacement is accepted. | archive, legacy, integrity |

---

## Architecture

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| ARCH-001 | Pipeline Structure Is Fixed | GenesisPrediction follows Observation → Trend → Signal → Scenario → Prediction, with Explanation, Vector Memory, FX Decision, and History Snapshot as supporting layers. | pipeline, architecture |
| ARCH-002 | WorldDate Uses Local Date | WorldDate uses LOCAL DATE because raw news files are saved by local date. | worlddate, morning_ritual |
| ARCH-003 | Vector Memory Is Reference Only | Qdrant/vector memory is searchable reference memory; it must never overwrite analysis or become authority. | vector_memory, qdrant, reference |
| ARCH-004 | Memory Is Promoted, Not Raw | Only decisions, rules, and durable insights are promoted; raw conversations, trials, and temporary logs are not authoritative memory. | memory, promotion |
| ARCH-005 | Decision Log Is Primary Memory Source | decision_log.md is the primary source for decision memory indexing. | memory, decision_log |
| ARCH-006 | build_vector_memory.py Is Single Entrypoint | Vector memory rebuild uses build_vector_memory.py as the single rebuild entrypoint. | vector_memory, scripts |
| ARCH-007 | Reference Memory Is Compacted For UI | Reference memory passed to UI is compacted by analysis/scripts; UI must not compact raw memory. | reference_memory, ui |
| ARCH-008 | VectorDB Must Separate Authority And Rationale Memory | decision_log entries and archive rationale must be indexed as separate reference memory types and must not be treated as equal authority. | vector_memory, authority, rationale |
| ARCH-009 | Archive Recall Is Context Only | archive recall may explain history and rationale but must not override current decision_log authority. | vector_memory, archive, recall |
| ARCH-010 | Downstream Layers Must Not Feed Upstream | Later pipeline layers must not be read by earlier layers; Prediction must not feed Trend/Signal/Scenario or create feedback loops. | pipeline, dependency, feedback_loop |

---

## Language / i18n

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| I18N-001 | Global i18n Architecture Is Analysis-Side | Translation and *_i18n generation happen in scripts/analysis; UI only selects and displays. | i18n, analysis, ui |
| I18N-002 | Language State Is Centrally Managed | LANG state is centrally managed like theme; pages do not directly own language state. | lang, theme, central_state |
| I18N-003 | UI Must Not Generate Language | UI must not translate, supplement, fallback-generate, compress, or reinterpret language content. | ui, i18n, language |
| I18N-004 | Runtime Text Must Not Compete With Static i18n | A DOM node must have one text responsibility; static labels and runtime content must not overwrite each other. | i18n, runtime_text |
| I18N-005 | Static Labels May Use Central Dictionary | Static labels may use central dictionary; dynamic runtime text must come from analysis *_i18n fields. | i18n, labels |
| I18N-006 | Prediction Output Must Preserve Structure | Prediction output must not use partial word-level translation fallback; unknown phrases remain raw unless explicitly mapped. | prediction, i18n, structure |
| I18N-007 | Scenario Labels Must Not Use Generic Translation | Scenario labels must be explicit canonical labels, not generic translation artifacts. | scenario, i18n, labels |
| I18N-008 | EN Is Internal SSOT For Language Architecture | English is the primary internal basis for generated i18n/artifacts; Japanese and Thai are supplementary display layers. | i18n, en, ssot |

---

## Prediction / Scenario

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| PRED-001 | Prediction Must Be Last Layer | Prediction is the final decision-grade summary; it must not replace Observation/Trend/Signal/Scenario. | prediction, architecture |
| PRED-002 | Scenario Engine Must Produce Causal Branches | Scenario output must be causal, branch-readable, and monitoring-linked, not template text. | scenario, causal, branch |
| PRED-003 | Scenario Drivers Must Be Cause-Oriented | Scenario key_drivers must contain causes, not outcomes, state labels, or scenario names. | scenario, drivers, cause |
| PRED-004 | Prediction Must Be Decision-Grade | Prediction must be a decision-grade conclusion, not a scenario restatement. | prediction, decision_grade |
| PRED-005 | Prediction Drivers Are Limited And Cause-Oriented | Prediction key_drivers should be short, limited, and cause-oriented. | prediction, drivers, cause |
| PRED-006 | Monitoring Priorities Follow Branch Logic | Monitoring priorities must preserve decision flow and branch logic, especially escalation and persistence before stabilization. | prediction, monitoring, branch_logic |
| PRED-007 | Scenario Driver Canonicalization Excludes Scenario Labels | Scenario labels such as base_case/best_case/worst_case must not enter driver canonicalization. | scenario, canonicalization |
| PRED-008 | Scenario Transmission Is Deterministic Per Branch | Scenario transmission chains must be deterministic and branch-specific. | scenario, transmission |
| PRED-009 | Scenario Narrative Uses Structured Drivers | Scenario narrative must be built from structured drivers, not raw tags. | scenario, narrative |
| PRED-010 | Scenario Narrative Outcomes Align With Branch Outcomes | Scenario narrative outcomes must align with branch expected outcomes. | scenario, outcomes |
| PRED-011 | Internal Scenario Tokens Are Snake Case | Internal scenario/transmission tokens must use snake_case. | scenario, tokens, snake_case |
| PRED-012 | Scenario Carries Invalidation Conditions | Scenario branches must carry invalidation conditions. | scenario, invalidation |
| PRED-013 | Scenario Engine Final Polish Is Baseline | The production-ready scenario baseline is causal branches + deterministic transmission + aligned narrative + snake_case tokens + invalidation. | scenario, milestone |

---

## Explanation

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| EXPL-001 | Explanation Is Mirror Of Prediction | Explanation mirrors prediction and must not reinterpret it or create new truth. | explanation, prediction, mirror |
| EXPL-002 | Watchpoints Must Not Mix Layers | Prediction monitoring_priorities take precedence; explanation must not mix scenario/signal watchpoints when prediction watchpoints exist. | watchpoints, explanation, prediction |
| EXPL-003 | Explanation Fields Mirror Prediction Fields | drivers, monitoring, implications, risks, and invalidation must mirror prediction fields directly. | explanation, mirror, structure |
| EXPL-004 | Explanation May Clarify Reading Only | Explanation may structure reading guidance and misread prevention, but must not add new causes, risks, or watchpoints. | explanation, no_new_truth |
| EXPL-005 | Explanation Drivers Are Pure Prediction Mirror | explanation.drivers mirror prediction.key_drivers / prediction.drivers without extra why/impact reconstruction. | explanation, drivers, mirror |
| EXPL-006 | Explanation Core Fields Are Pure Prediction Mirror | Explanation core fields mirror prediction directly without structured reinterpretation. | explanation, core_fields, mirror |

---

## Operations / Deploy

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| OPS-001 | Deploy Target Is Snapshot | LABOS is a distribution snapshot; Git + analysis/data remain authoritative. | deploy, labos, snapshot |
| OPS-002 | Deploy Is Full Replacement | Deploy must fully replace target state and must not overlay stale files. | deploy, full_replacement |
| OPS-003 | Deploy Must Be Target-Isolated | Deploy must only operate inside the intended LABOS target and must not affect other hosted sites. | deploy, conoha, safety |
| OPS-004 | Deploy Payload Self-Deletion Guard | Cleanup logic must not delete the deploy payload before extraction. | deploy, payload, guard |
| OPS-005 | Deploy Verification Must Follow Deploy | Deploy success is not final; verify_deploy.py/local-vs-public comparison must pass. | deploy, verify |
| OPS-006 | Morning Ritual Chain Is Formal | Morning Ritual → post checks → deploy → verify is the formal end-to-end operational chain. | morning_ritual, deploy, verify |
| OPS-007 | Build And View Environments Are Separated | Home/build PC generates analysis/data; company/view PC consumes and verifies only. | environment, build, view |
| OPS-008 | Company PC Must Not Regenerate Analysis/Data | Company PC must not run Morning Ritual or regenerate analysis/data. | environment, no_build |
| OPS-009 | analysis/data USB Sync Is Valid Transport | Whole analysis/data sync from build environment to view environment is valid; do not regenerate on view side. | sync, transport |
| OPS-010 | Git Restore Is Destructive Rollback | git restore is destructive rollback and must only be used after explicit rollback decision. | git, restore, rollback |
| OPS-011 | Detached HEAD Work Is Not Trusted Final State | Detached HEAD work is not final until returned to main and committed/stashed intentionally. | git, detached_head |
| OPS-012 | Local Cache Failure Is Operational Incident | fastembed/local cache failures are operational incidents, not architecture failures. | cache, fastembed, incident |
| OPS-013 | Automation Must Expose Phase Status And Exit Code | Unattended automation must expose per-phase OK/FAIL/SKIP and unified final exit code. | automation, status, exit_code |
| OPS-014 | Vector Rebuild Self-Healing Is Valid | WARN → rebuild → re-check → OK for vector freshness is valid self-healing behavior. | vector_memory, self_healing |
| OPS-015 | Dirty Repo Guard Enforced | Run scripts must execute on a clean working tree. | git, dirty_guard |
| OPS-016 | Pre-Run Commit Required | Commit before run is mandatory to satisfy dirty guard and preserve reproducibility. | git, commit, operations |
| OPS-017 | PowerShell Switch Parameters Do Not Receive Boolean Values | PowerShell switch parameters are enabled by presence and must not receive explicit boolean values. | powershell, switch |
| OPS-018 | Cross-Platform PowerShell Prefers pwsh On Core | PowerShell Core environments must dynamically resolve pwsh instead of powershell. | powershell, github_actions |
| OPS-019 | NoLLM Morning Ritual GitHub Actions Trial Succeeded | NoLLM GitHub Actions workflow can support iPad-driven LABOS updates when SSH restrictions are resolved. | github_actions, nollm, labos |
| OPS-020 | Deploy Verify Is Technical, Not Semantic Truth | verify_deploy.py confirms deployed artifacts match local artifacts; it does not prove that generated meaning, dates, or pipeline logic are correct. | deploy, verify, semantic_integrity |

---

## Data / Analysis

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| DATA-001 | Sentiment Output Is Semantic | Sentiment output includes theme_tags, signal_tags, risk_drivers, and impact_tags for Prediction/Scenario use. | sentiment, semantic |
| DATA-002 | World View Summary Is Structured First | World view summary derives from structured summary, not malformed upstream free text. | world_view, summary |
| DATA-003 | Prediction Uses Semantic Analysis Fields | Prediction consumes semantic analysis fields, not score-only sentiment. | prediction, semantic |
| DATA-004 | Daily Summary Is Count-Based | daily_summary_latest summary must be derived from count-based structured fields and not contradict today.count. | summary, count |
| DATA-005 | Health Output Path Matches SSOT Path | build_data_health.py output must align with analysis/health_latest.json when guards verify that path. | health, ssot, path |
| DATA-006 | World Latest Pointer Must Sync During News Publish | Publishing daily world news must synchronize data/world_politics/analysis/latest.json with the dated raw source so downstream view/global status artifacts do not drift to stale as_of dates. | world_politics, latest_pointer, as_of, publish |
| DATA-007 | Dated Raw Source Is Authority Over latest.json | When a dated raw world news source exists for the requested/local date, pipeline truth selection must prefer the dated source over analysis/latest.json to prevent stale as_of drift. | world_politics, authority, latest_pointer, stale_prevention |

---

## UI / Public Release

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| UI-001 | UI Must Not Silently Mask Missing Data | Missing data must be visible as loading/missing/unavailable, not hidden as normal output. | ui, missing_data, silent_failure |
| UI-002 | Release Requires Analysis Completeness | Deploy/release requires necessary latest JSON and *_i18n keys; UI fixes must not cover incomplete analysis. | release, analysis, completeness |
| UI-003 | Digest Summary i18n Generated In Analysis | Digest summary_i18n is generated in analysis and displayed by UI only. | digest, i18n |
| UI-004 | Prediction History Syncs To Data Layer For UI | Prediction history must be synced to data layer paths needed by the UI distribution. | history, data_layer, ui |
| UI-005 | Local Server And Distribution Are Distinct | Local dev server structure and dist/deploy structure must not be confused. | distribution, local_server |
| UI-006 | UI 404 Debug Starts From Distribution Layer | UI 404 issues must be debugged from distribution/build output before page logic. | ui, debug, distribution |
| UI-007 | GUI Final Audit Completed | GUI final audit established the public UI baseline. | ui, audit |
| UI-008 | Pre-Deploy Payload Freshness Check Required | Deploy payload must be checked for freshness before deployment. | deploy, payload, freshness |
| UI-009 | Favicon And OGP Handling In Static Deployment | Static deploy must preserve favicon and OGP asset paths. | seo, ogp, favicon |
| UI-010 | Home Is Route-First Public Landing Page | Home must guide users to Digest, Overlay, and Prediction as route-first public landing page. | home, landing, public |
| UI-011 | Prediction Static Text Resolves Locally | Prediction page static labels resolve from page-local UI_TEXT when required, not conflicting shared runtime routing. | prediction, ui_text, i18n |

---

## Policy / Public Content

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| POLICY-001 | News Content Must Not Be Reproduced In Full | GenesisPrediction summarizes and links news; it must never reproduce full articles or large source text. | news, copyright, policy |
| POLICY-002 | Policy Docs Are Human-Facing; AI Rules Are Compressed | Detailed policy docs may exist for humans, but AI-effective rules must be compressed into decision_log and indexed. | policy, decision_log |

---

## Thread Governance

| ID | Decision | Binding Rule | Tags |
|---|---|---|---|
| THREAD-001 | Thread Objective Freeze And Completion Boundary | Each thread must freeze objective and completion boundary to avoid infinite expansion. | thread, scope, completion |

---

# 4. Archive Reference

Historical rationale archive:

```text
docs/archive/decision_rationale/legacy_decision_log_2026-05-09.md
docs/archive/decision_rationale/decision_log_consolidation_map.md
docs/archive/decision_rationale/decision_log_consolidation_report.md
docs/archive/decision_rationale/decision_log_rationale_archive_2026-05-09.md
```

Use archive only for:

- why a decision was made
- historical reconstruction
- audit trail
- context when updating a current decision

Do not use archive as:

- current authority
- UI source
- analysis truth
- replacement for current decision_log entries

---

# 5. Maintenance Rules

1. Add new decisions as compact rows in the relevant section.
2. Put long rationale in `docs/archive/decision_rationale/` when needed.
3. Update `decision_index.md` with one navigation entry per decision.
4. Rebuild VectorDB after decision_log/index/archive updates when the project workflow requires it.
5. Keep entries short enough for humans and AI to govern from them.
6. When an incident reveals a new architectural constraint, record the compact binding rule here and place long incident narrative in archive only if needed.

---

END OF DOCUMENT
