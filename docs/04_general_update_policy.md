# General Update Policy (Genesis Assistant)

## Purpose

Define when knowledge should be updated, when it should remain unchanged, and how to maintain consistency over time.

---

## Core Principle

Not all new information should overwrite existing knowledge.

Stability is more important than frequent updates.

---

## When to Update

### 1. Environment Changes

Examples:

- OS change
- hardware upgrade
- tool replacement
- model configuration changes

Condition:

- affects future outputs or behavior

---

### 2. Confirmed Better Decisions

Examples:

- improved workflow
- better tool selection
- refined architecture
- proven optimization

Condition:

- clearly better than previous decision
- tested or validated

---

### 3. Repeated Patterns

Examples:

- recurring user behavior
- repeated preferences
- consistent usage patterns

Condition:

- appears multiple times
- stable over time

---

### 4. Correction of Errors

Examples:

- wrong assumptions
- outdated info
- incorrect conclusions

Condition:

- new information is verified

---

## When NOT to Update

### 1. One-Time Events

Examples:

- temporary fixes
- single-use scripts
- experimental results

---

### 2. Unverified Information

Examples:

- guesses
- incomplete conclusions
- early-stage ideas

---

### 3. Emotional or Casual Context

Examples:

- frustration
- opinions without action
- temporary thoughts

---

### 4. No Clear Impact

Examples:

- information that does not affect future decisions
- redundant details

---

## Update Strategy

### Prefer "Refinement" Over "Replacement"

- Modify existing knowledge
- Avoid deleting useful history
- Preserve continuity

---

### Keep History Implicit

- Do not store all past versions
- Keep only the best current state

---

### Avoid Frequent Rewrites

- Stability > freshness
- Update only when meaningful

---

## Consistency Rule

After update:

- New knowledge must not contradict:
  - core principles
  - existing stable rules
  - verified decisions

If contradiction occurs:

- Resolve explicitly
- Prefer latest verified truth

---

## Decision Threshold

Before updating, ask:

1. Is this reusable?
2. Is this stable?
3. Will this improve future responses?

If ANY answer is "No":

→ Do NOT update

---

## Minimal Update Principle

- Smaller updates are better
- Avoid large-scale rewrites unless necessary

---

## Qdrant Preparation Rule

This policy ensures:

- clean embeddings
- low noise
- high retrieval quality

Only stable and meaningful updates should enter the system.

---

## Summary

Update ONLY when:

- stable
- verified
- reusable
- improves future outputs

Do NOT update when:

- temporary
- uncertain
- emotional
- irrelevant