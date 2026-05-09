# Decision Rationale Archive (GenesisPrediction v2)

Status: Active
Purpose: Historical rationale archive for decision_log consolidation and long-form operational reasoning

---

# Role

This directory stores rationale and historical context that should not live inside the compact authoritative decision log.

```text
docs/core/decision_log.md = current operational decision authority
docs/core/decision_index.md = navigation only
docs/archive/decision_rationale/ = historical rationale only
VectorDB = reference recall only
```

---

# Files

```text
legacy_decision_log_2026-05-09.md
decision_log_rationale_archive_2026-05-09.md
decision_log_consolidation_map.md
decision_log_consolidation_report.md
README.md
```

---

# Rules

1. Archive files explain history; they do not override current decisions.
2. Current binding rules belong in `docs/core/decision_log.md`.
3. Long rationale belongs here only when needed.
4. VectorDB may index this directory as reference memory.
5. Recall from this directory is context, not authority.

---

END OF DOCUMENT
