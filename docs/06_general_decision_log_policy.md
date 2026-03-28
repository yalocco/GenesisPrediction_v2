# General Decision Log Policy

## Purpose

Define when a conversation outcome should be proposed for inclusion in the general decision log.

---

## Core Rule

The assistant may propose a decision_log entry only when all of the following are true:

1. The decision has future impact
2. The decision is reusable
3. The decision is sufficiently clear
4. The decision is not temporary

The assistant must NOT assume consent.
The user must approve before the entry is added.

---

## Proposal Rule

When a decision matches the conditions, the assistant should say:

「これは重要な判断です。decision_logに追加しますか？」

Only after user approval should the assistant generate the entry.

---

## Good Candidates

- architecture choices
- workflow rules
- stable operating policies
- preferred tool roles
- memory / RAG / logging rules
- durable response style rules
- separation of responsibilities
- accepted / rejected long-term approaches

---

## Bad Candidates

- temporary fixes
- debug steps
- one-time experiments
- casual opinions
- incomplete ideas
- low-impact preferences

---

## Decision Threshold

A decision should be proposed only if it is likely to help future conversations or future work.

If uncertain, do not propose.

---

## Approval Rule

The user has final authority.

Possible approval examples:

- 入れる
- 追加して
- decision_logに入れる
- yes

Possible rejection examples:

- 入れない
- 今回は不要
- no

---

## Output Rule

When approved, generate the entry in the standard decision log format:

- Date
- Context
- Decision
- Reason
- Alternatives Considered
- Impact

---

## Summary

The assistant should:
- detect important decisions
- propose logging
- wait for approval
- then generate the final entry

This is semi-automatic logging, not full automatic logging.