# Decision Index (GenesisPrediction v2)

Status: Active
Purpose: decision_log の検索効率を向上させるための軽量インデックス
Last Updated: 2026-04-10

---

# 0. Purpose

このファイルは

```text
decision_log.md の検索補助
```

として使用する。

重要:

```text
decision_index は真実ではない
decision_log が唯一の正本である
```

---

# 1. Rules

## Rule 1

```text
1 decision = 1 entry
```

## Rule 2

```text
1 entry = 4行構成
```

- date
- title
- tags
- rule

## Rule 3

```text
長文禁止
説明禁止
要約禁止
```

## Rule 4

```text
source は必ず decision_log.md を指す
```

---

# 2. Index Entries

---

## CORE | Analysis Is Single Source of Truth

tags: analysis, ssot, architecture

rule: analysis is the single source of truth and ui must not override it

source: docs/core/decision_log.md

---

## CORE | UI Is Display Only

tags: ui, display_only, architecture

rule: ui must not compute, decide, translate, or generate meaning

source: docs/core/decision_log.md

---

## CORE | Full File Delivery Only

tags: generation, full_file, integrity

rule: diff proposals are prohibited and full files are required

source: docs/core/decision_log.md

---

## CORE | Existing File Must Be Verified

tags: generation, integrity, verification

rule: do not generate from guesswork when an existing file has not been verified

source: docs/core/decision_log.md

---

## CORE | Vector Memory Is Reference Only

tags: vector_memory, reference, architecture

rule: vector memory must be reference-only and must not overwrite analysis

source: docs/core/decision_log.md

---

## 2026-04-04 | Explanation Is a Mirror of Prediction

tags: explanation, prediction, mirror

rule: analysis/prediction/prediction_latest.json

source: docs/core/decision_log.md

---

## 2026-04-04 | Watchpoints Must Not Be Mixed Across Layers

tags: watchpoints, prediction, explanation

rule: scripts/build_prediction_explanation.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Runtime UI Text Must Not Compete With Static i18n

tags: runtime, ui, text, not, compete

rule: app/static/*.html

source: docs/core/decision_log.md

---

## 2026-04-04 | Build Environment（自宅PC）

tags: build, environment, pc

rule: llmあり

source: docs/core/decision_log.md

---

## 2026-04-04 | View Environment（会社PC）

tags: view, environment, pc

rule: ui確認

source: docs/core/decision_log.md

---

## 2026-04-04 | Automation Must Expose Phase Status and Unified Exit Code

tags: automation, expose, phase, status, unified

rule: scripts/run_morning_ritual_with_checks.ps1

source: docs/core/decision_log.md

---

## 2026-04-04 | Automatic Vector Memory Rebuild Is Accepted as Self-Healing in Pipeline

tags: automatic, vector, memory, rebuild, accepted

rule: vector memory freshness が warn の場合

source: docs/core/decision_log.md

---

## 2026-03-27 | UI i18n Template Standardization

tags: ui, i18n, template, standardization

rule: - adopt prediction-based ui i18n template

source: docs/core/decision_log.md

---

## 2026-03-27 | 結論

tags: decision

rule: vector memory は

source: docs/core/decision_log.md

---

## 2026-03-27 | 理由

tags: decision

rule: - 既存の責務分離（analysis / scripts / ui）がすでに完成している

source: docs/core/decision_log.md

---

## 2026-03-27 | 方針

tags: decision

rule: build_vector_memory.py を単一入口とする

source: docs/core/decision_log.md

---

## 2026-03-27 | 許可される将来拡張

tags: decision

rule: langchain は将来的に以下用途に限定して検討可能

source: docs/core/decision_log.md

---

## 2026-03-27 | 非交渉ルール

tags: decision

rule: langchain は

source: docs/core/decision_log.md

---

## 2026-04-02 | Sentiment Semantic Enrichment (B-1〜B-4)

tags: sentiment, semantic, enrichment, b, 1

rule: theme_tags

source: docs/core/decision_log.md

---

## 2026-04-02 | World View Structured Summary Enforcement

tags: world, view, structured, summary, enforcement

rule: summary_structured = 正

source: docs/core/decision_log.md

---

## 2026-04-02 | Prediction Must Use Semantic Analysis Fields

tags: prediction, use, semantic, analysis, fields

rule: theme_tags

source: docs/core/decision_log.md

---

## 2026-04-04 | Deploy Hardening (Full Replacement, Target-Only, Permission-Aware)

tags: deploy, hardening, full, replacement, target

rule: - labos.soma-samui.com 以外のディレクトリを操作しない

source: docs/core/decision_log.md

---

## 2026-04-04 | Deploy Payload Self-Deletion Guard

tags: deploy, payload, self, deletion, guard

rule: cleanup 処理で deploy payload（tar）を除外する

source: docs/core/decision_log.md

---

## 2026-04-04 | Deploy Permission Constraints (Conoha)

tags: deploy, permission, constraints, conoha

rule: - ディレクトリ自体の削除ではなく中身のみ削除する

source: docs/core/decision_log.md

---

## 2026-04-04 | Full File Integrity Reinforcement (Line Count & Copy Safety)

tags: full, file, integrity, reinforcement, line

rule: - 元ファイルより大幅に行数が減る場合は生成禁止

source: docs/core/decision_log.md

---

## 2026-04-04 | Deploy Verification Must Follow Deploy

tags: deploy, verify, operations

rule: deploy 成功表示だけで完了とみなさない

source: docs/core/decision_log.md

---

## 2026-04-04 | Morning Ritual End-to-End Chain Is Valid

tags: operations, ritual, deploy, verify

rule: run_morning_ritual.ps1

source: docs/core/decision_log.md

---

## 2026-04-04 | Prediction Enhancement Phase 2 Completion (Recall Alignment & Text Quality)

tags: prediction, enhancement, phase, 2, completion

rule: prediction は vector memory を補助情報として参照する

source: docs/core/decision_log.md

---

## 2026-04-04 | Dirty Repo Guard Enforcement (Run Requires Clean Working Tree)

tags: dirty, repo, guard, enforcement, run

rule: scripts/run_daily_with_publish.ps1

source: docs/core/decision_log.md

---

## 2026-04-04 | Pre-Run Commit Rule (Operational Requirement)

tags: pre, run, commit, rule, operational

rule: run 前は必ず commit を行う

source: docs/core/decision_log.md

---

## 2026-04-04 | PowerShell Switch Parameter Rule (No Boolean Value Passing)

tags: powershell, switch, parameter, rule, no

rule: powershell scripts

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Engine Must Produce Causal Branches, Not Templates

tags: scenario, causal, branch, watchpoints

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Drivers Must Be Cause-Oriented

tags: scenario, drivers, cause

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Prediction Must Be Decision-Grade, Not Scenario Restatement

tags: prediction, decision, architecture, scenario

rule: scripts/prediction_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Prediction Drivers Must Be Limited and Cause-Oriented

tags: prediction, drivers, cause

rule: scripts/prediction_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Prediction Monitoring Priorities Must Follow Branch Logic

tags: prediction, monitoring, branch_logic

rule: scripts/prediction_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Explanation Must Be Mirror-Only Across Structured Fields

tags: explanation, mirror, structure

rule: scripts/build_prediction_explanation.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Explanation May Clarify Reading, But Must Not Create New Truth

tags: explanation, mirror, truth

rule: headline

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Driver Canonicalization Must Exclude Scenario Labels

tags: scenario, drivers, canonicalization

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Prediction Enhancement (Cause-Oriented Scenario + Decision-Grade Prediction) Is Completed

tags: prediction, scenario, milestone

rule: analysis/prediction/scenario_latest.json

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Transmission Must Be Deterministic Per Branch

tags: scenario, transmission, deterministic, branch

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Narrative Must Be Built From Structured Drivers, Not Raw Tags

tags: scenario, narrative, drivers

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Narrative Outcomes Must Align With Branch Outcomes

tags: scenario, narrative, outcomes, branch

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Internal Scenario / Transmission Tokens Must Be Snake Case

tags: scenario, tokens, snake_case, i18n

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Must Carry Invalidation Conditions

tags: scenario, invalidation, monitoring

rule: scripts/scenario_engine.py

source: docs/core/decision_log.md

---

## 2026-04-04 | Scenario Engine Final Polish Completed

tags: scenario, production_ready, milestone

rule: analysis/prediction/scenario_latest.json

source: docs/core/decision_log.md

---

## 2026-04-05 | Markdown Editing Must Use Download-Based Full File Workflow

tags: markdown, workflow, download, integrity

rule: docs/*.md

source: docs/core/decision_log.md

---

## 2026-04-05 | 背景

tags: decision

rule: コードブロック崩壊

source: docs/core/decision_log.md

---

## 2026-04-05 | 新ルール

tags: decision

rule: .md ファイルはブラウザコピペ編集を禁止する

source: docs/core/decision_log.md

---

## 2026-04-05 | 必須運用

tags: decision

rule: 完全ファイルをダウンロード形式で受け取る

source: docs/core/decision_log.md

---

## 2026-04-05 | 禁止事項

tags: decision

rule: ブラウザ上での直接編集

source: docs/core/decision_log.md

---

## 2026-04-05 | 理由

tags: decision

rule: markdown は構造依存が強く、

source: docs/core/decision_log.md

---

## 2026-04-05 | 既存ルールとの関係

tags: decision

rule: 完全ファイルのみ

source: docs/core/decision_log.md

---

## 2026-04-05 | 本質

tags: decision

rule: markdown はコードである

source: docs/core/decision_log.md

---

## 2026-04-05 | Prediction Output Must Preserve Structure (No Partial Translation)

tags: prediction, i18n, translation, structure

rule: decision:

source: docs/core/decision_log.md

---

## 2026-04-05 | Scenario Labels Must Not Use Generic Translation

tags: scenario, i18n, labels

rule: decision:

source: docs/core/decision_log.md

---

## 2026-04-05 | Prediction Enhancement v4 Completed

tags: prediction, milestone, v4

rule: summary:

source: docs/core/decision_log.md

---

## 2026-04-05 | Prediction Layer i18n Must Be Fully Resolved in Analysis (Structure Fix)

tags: prediction, i18n, analysis

rule: scripts/prediction_engine.py

source: docs/core/decision_log.md

---

## 2026-04-05 | Prediction Must Carry Structured Semantics (No Meaning Gap)

tags: prediction, structure, explanation, ui

rule: scripts/prediction_engine.py

source: docs/core/decision_log.md

---

## 2026-04-05 | System Completion and Phase Transition to Operation

tags: operations, completion, ritual

rule: scripts/run_morning_ritual_with_checks.ps1

source: docs/core/decision_log.md

---

## 2026-04-07 | Prediction History Must Be Synced to data Layer for UI

tags: history, data_layer, ui

rule: analysis/prediction/history/*

source: docs/core/decision_log.md

---

## 2026-04-07 | Local Server and Distribution Structure Must Be Strictly Distinguished

tags: distribution, local_server, ui

rule: decision: local development server and distribution (dist) structure must not be confused

source: docs/core/decision_log.md

---

## 2026-04-07 | UI 404 Debug Must Start From Distribution Layer

tags: ui, debug, distribution

rule: decision: ui 404 errors must be debugged from distribution layer, not ui layer

source: docs/core/decision_log.md

---

## 2026-04-08 | GUI Final Audit Completed

tags: ui, audit, stability

rule: 全ページで local / labos 一致確認済み

source: docs/core/decision_log.md

---

## 2026-04-08 | Pre-deploy Payload Freshness Check Is Mandatory

tags: deploy, payload, freshness

rule: deploy前に dist/labos_deploy の snapshot を確認する

source: docs/core/decision_log.md

---

## 2026-04-08 | EN as SSOT (Language Architecture Finalization)

tags: i18n, language, ssot

rule: decision:

source: docs/core/decision_log.md

---

## 2026-04-08 | Explanation Pure Mirror Hardening

tags: explanation, mirror, hardening

rule: decision:

source: docs/core/decision_log.md

---

## 2026-04-08 | Structured Truth Consolidation

tags: prediction, structure, truth

rule: decision:

source: docs/core/decision_log.md

---

## 2026-04-08 | Prediction Enhancement Phase1

tags: prediction, enhancement, phase1

rule: decision:

source: docs/core/decision_log.md

---

## 2026-04-08 | Decision Action Hardening (Branch-Linked Actions, Triggers, Outcomes)

tags: decision, action, hardening, branch, linked

rule: scripts/prediction_engine.py

source: docs/core/decision_log.md

---

## 2026-04-09 | Daily Summary Materialization Must Be Count-Based

tags: summary, materialization, count, structured

rule: daily_summary_latest.json summary must be derived from today.count and must not contradict it

source: docs/core/decision_log.md

---


---

## 2026-04-10 | Explanation Drivers Must Be Pure Prediction Mirror

tags: explanation, drivers, mirror, prediction

rule: explanation.drivers must mirror prediction.key_drivers / prediction.drivers without why / impact

source: docs/core/decision_log.md


---

## 2026-04-10 | Explanation Core Fields Must Be Pure Prediction Mirror

tags: explanation, mirror, prediction, monitor, implications, risks, invalidation

rule: explanation core fields must mirror prediction fields directly without structured reinterpretation

source: docs/core/decision_log.md



## 2026-04-10 | Prediction Monitoring Priorities Ordering Must Preserve Decision Flow

tags: prediction, monitoring, ordering, decision_flow

rule: monitoring_priorities must be ordered as escalation → persistence → downstream confirmation → stabilization

source: docs/core/decision_log.md


## 2026-04-19 | Home Must Be Route-First Public Landing Page

tags: home, landing, routes, public_release, ui

rule: home must be route-first and lead users toward digest, overlay, and prediction

source: docs/core/decision_log.md

---

## 2026-04-19 | Prediction Page Static UI Text Must Resolve Locally

tags: prediction, i18n, static_labels, local_ui_text

rule: prediction.html static labels must resolve from page-local UI_TEXT, not shared translation routing

source: docs/core/decision_log.md

---


## 2026-04-19 | News Content Must Never Be Reproduced In Full

tags: news, copyright, summary, linking, public_release

rule: news content must never be reproduced in full; only summarized, linked, and transformed into analysis

source: docs/core/decision_log.md

---

## 2026-04-19 | Policy Documents Are Human-Facing; AI Rules Must Be Compressed Into Decision Log

tags: policy, decision_log, ai, governance

rule: detailed policy docs are human-facing and AI-effective rules must be compressed into decision_log

source: docs/core/decision_log.md

---

# 3. Notes

このファイルは以下用途で使用される：

```text
vector memory の高速検索
AI の意思決定参照
設計判断の一覧確認
```

重要:

```text
意味の解釈は decision_log を参照する
このファイル単体で判断しない
```

---

END OF FILE

---


## 2026-04-15 | Translation Pipeline Explicit Invocation

tags: translation, pipeline, invocation

rule: translation requires explicit parameters and is not implicit

source: docs/core/decision_log.md


---

END OF FILE
