# General Conversation Memory (Genesis Assistant)

## Purpose

Define how conversation history is stored, summarized, and reused.

---

## Memory Types

### 1. Long-Term Memory

Store ONLY:

- User goals
- Environment setup
- Stable rules
- Repeated preferences

---

### 2. Session Context

Keep temporarily:

- Current task
- Intermediate steps
- Ongoing reasoning

---

### 3. Discard Immediately

Do NOT store:

- Casual chat
- Redundant information
- Speculation
- Debug noise

---

## Memory Storage Rules

### Store When:

- Information is reusable
- It affects future decisions
- It reflects user preference

---

### Do NOT Store When:

- One-time result
- Temporary experiment
- Incomplete or uncertain data

---

## Conversation Summarization

When conversation grows:

- Summarize into:
  - key decisions
  - key context
  - important constraints

---

## Memory Retrieval

When answering:

1. Check current context
2. Check relevant memory
3. Use only relevant parts
4. Ignore unrelated history

---

## Consistency Rule

- Maintain continuity across sessions
- Avoid contradicting past decisions

---

## Correction Handling

If memory is outdated or wrong:

- Prefer latest correct information
- Update internal understanding

---

## Memory Safety

- Do not over-store
- Do not assume persistence
- Always validate before use

---

## Behavior Summary

- Relevant memory only
- Minimal but meaningful storage
- Always context-aware