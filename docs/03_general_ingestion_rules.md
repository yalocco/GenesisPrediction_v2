# General Ingestion Rules (Genesis Assistant)

## Purpose

Define what should be added to the general knowledge base, what should be excluded, and how information should be organized for stable retrieval.

---

## Core Principle

The knowledge base is not a dump folder.

Only add information that improves:

- continuity
- decision support
- reproducibility
- useful recall

---

## What to Include

### 1. Stable User Preferences

Examples:

- preferred language
- preferred response style
- work habits
- output format preferences

Condition:

- likely to remain useful across future conversations

---

### 2. Long-Term Environment Information

Examples:

- OS
- hardware
- main tools
- local AI setup
- Docker usage
- editor / shell preferences

Condition:

- important for future technical answers

---

### 3. Reusable Decision Records

Examples:

- important tool choices
- workflow decisions
- preferred model roles
- accepted / rejected approaches

Condition:

- decision has future impact

---

### 4. Reusable Thinking Rules

Examples:

- accuracy over speed
- no guessing
- structured step-by-step approach
- complete files preferred

Condition:

- affects how the assistant should respond in future

---

### 5. Compressed Conversation Memory

Examples:

- recurring goals
- repeated concerns
- durable constraints
- important conclusions

Condition:

- summarized, not raw chat logs

---

## What NOT to Include

### 1. Temporary Logs

Examples:

- debug output
- shell logs
- test results
- transient failures

Reason:

- too noisy
- low long-term value

---

### 2. Raw Conversation Dumps

Examples:

- full chat exports
- repeated back-and-forth
- casual discussion logs

Reason:

- retrieval quality degrades
- too much noise

---

### 3. One-Time Facts

Examples:

- today’s temporary result
- one-off experiment
- disposable values

Reason:

- not reusable enough

---

### 4. Unverified or Speculative Notes

Examples:

- guesses
- incomplete interpretations
- uncertain summaries

Reason:

- increases hallucination risk

---

### 5. Project-Specific Rules in the General KB

Examples:

- GenesisPrediction-only architecture laws
- SST rules tied only to one project
- project-specific contracts

Reason:

- should remain separated in project knowledge

---

## File Design Rules

### 1. One File = One Theme

Good:

- personal style
- decision style
- conversation memory

Bad:

- mixed notes
- random collections
- everything in one file

---

### 2. Keep Files Short and Clear

Prefer:

- compact summaries
- reusable rules
- direct statements

Avoid:

- long essays
- repeated explanations
- unnecessary background

---

### 3. Use Explicit File Names

Good examples:

- 00_general_ai_core.md
- 01_general_decision_style.md
- 02_general_conversation_memory.md
- 03_general_ingestion_rules.md

---

## Update Rules

### Add a file when:

- it improves future conversations
- it contains durable knowledge
- it helps preserve consistency

### Revise a file when:

- the rule changed
- the environment changed
- the previous summary became outdated

### Do not update when:

- the information is temporary
- the information is noisy
- the value is unclear

---

## Retrieval Priority

When answering, prefer:

1. current user request
2. relevant stable knowledge
3. relevant decision records
4. summarized memory
5. general reasoning

---

## Qdrant Preparation Rule

This knowledge base should be clean enough to be vectorized later.

That means:

- no raw noise
- no duplicated files
- no unclear notes
- no temporary logs

Only compact, meaningful, reusable knowledge should remain.

---

## Summary

Include:

- stable preferences
- environment
- decision records
- reusable rules
- compressed memory

Exclude:

- logs
- dumps
- temporary facts
- speculation
- project-only rules