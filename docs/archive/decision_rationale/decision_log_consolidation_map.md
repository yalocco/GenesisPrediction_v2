# Decision Log Consolidation Map (GenesisPrediction v2)

Status: Active
Purpose: Map the authority/archive separation applied to GenesisPrediction decision_log.md
Date: 2026-05-09

---

# 0. Purpose

This document explains how the former long-form `decision_log.md` was consolidated into a compact authority record while preserving historical rationale.

It is not the authority source itself.

```text
docs/core/decision_log.md = current operational decision authority
docs/core/decision_index.md = navigation only
docs/archive/decision_rationale/ = historical rationale and migration evidence
VectorDB = reference recall only
```

---

# 1. Consolidation Rule

The consolidation follows this hierarchy:

```text
authority
≠
archive
≠
vector recall
```

Meaning:

- authority decides current operational rules
- archive preserves why and how decisions developed
- vector recall helps retrieve references but never becomes authority

---

# 2. File Mapping

| Former content type | New location | Authority status |
|---|---|---|
| current binding rules | `docs/core/decision_log.md` | authoritative |
| searchable decision titles | `docs/core/decision_index.md` | navigation only |
| full legacy decision log | `docs/archive/decision_rationale/legacy_decision_log_2026-05-09.md` | historical rationale only |
| rationale archive copy | `docs/archive/decision_rationale/decision_log_rationale_archive_2026-05-09.md` | historical rationale only |
| consolidation map | `docs/archive/decision_rationale/decision_log_consolidation_map.md` | migration reference only |
| consolidation report | `docs/archive/decision_rationale/decision_log_consolidation_report.md` | migration reference only |
| archive README | `docs/archive/decision_rationale/README.md` | usage guide only |

---

# 3. Authority Preservation

The compact `decision_log.md` preserves binding rules by converting long narrative decisions into concise operational rows.

The archive preserves the original long-form material so that no historical reasoning is lost.

The line-count reduction is therefore intentional and valid because:

```text
large decision_log reduction
=
authority extraction + rationale archive preservation
≠
content loss
```

---

# 4. Archive Usage

Archive files may be used for:

- historical reconstruction
- rationale review
- audit trail
- understanding why a rule exists
- rebuilding context when updating a decision

Archive files must not be used for:

- overriding current decision_log entries
- acting as UI source
- acting as analysis truth
- replacing compact authority decisions

---

# 5. VectorDB Mapping

Recommended VectorDB memory classification:

| Source | Recommended memory_type | Role |
|---|---|---|
| `docs/core/decision_log.md` | `decision_authority` | current binding decision recall |
| `docs/core/decision_index.md` | `decision_navigation` | search/navigation recall |
| `docs/archive/decision_rationale/*.md` | `decision_rationale_archive` | historical rationale recall |
| prediction/scenario history | `prediction_snapshot` / `scenario_snapshot` | operational history recall |

Important rule:

```text
A recall hit from decision_rationale_archive is context only.
A recall hit from decision_authority points to current rules.
```

---

# 6. Maintenance Rule

When adding future decisions:

1. Add the current binding rule to `docs/core/decision_log.md`.
2. Add one navigation entry to `docs/core/decision_index.md`.
3. Put long reasoning in `docs/archive/decision_rationale/` only when needed.
4. Rebuild VectorDB after updating authority/index/archive files.
5. Never let archive rationale become the effective current rule.

---

END OF DOCUMENT
