# GenesisPrediction Data i18n Classification

## Purpose
Define which fields should be handled by dictionary-based multilingual support versus free-text translation, under the GenesisPrediction architecture rules.

This document is the working classification baseline for Data i18n implementation.

---

## Absolute Rules

- SSOT = analysis outputs only
- UI must NOT translate
- UI must read and display `*_i18n` only
- Classification, interpretation, translation, and fallback policy belong to analysis / scripts
- Language state must be centrally managed
- Free-text translation is optional in the short term; English fallback is allowed only from analysis-side prepared fields, never from UI-side translation logic

---

## A. Dictionary-based Fields

These are stable, controlled, short vocabulary fields that should be translated by dictionary first.

### A1. Status / Regime / Decision Fields
- `risk`
- `global_risk`
- `regime`
- `status`
- `health`
- `fx_status`
- `review`
- `action_bias`
- `dominant_scenario`
- `sentiment`
- `sentiment_label`
- `reference_memory.status`

### A2. Labels / Classification Fields
- `category`
- `label`
- `section title`
- `scenario_structure.dominant`
- `scenario_structure.balance`
- `history drift labels`
- `source status`
- `signal layer status`
- `scenario layer status`

### A3. Signal / Theme Names
- `economic_signals[]`
- `geopolitical_signals[]`
- `key driver labels`
- `monitoring priority labels`
- `outcome labels`
- `historical pattern names`
- `historical analog names`

### A4. FX / Prediction Short Controlled Vocabulary
- `CAUTION`
- `GUARDED`
- `STABLE`
- `WARN`
- `OK`
- `LOW`
- `MIX`
- `HIGH`
- `base_case`
- `upside`
- `downside`
- `bullish`
- `bearish`
- `neutral`
- `positive`
- `negative`
- `mixed`
- `unknown`

### A5. Short Fixed UI Terms
- `No data`
- `Unavailable`
- `Open JSON`
- `Open CSV`
- `Loading`
- `articles`
- `summary`
- `highlights`
- `confidence`
- `risk drift`
- `scenario shift`
- `monitoring`
- `expected outcomes`
- `historical context`

### A6. Initial Signal Vocabulary Candidates
- `Energy price volatility`
- `Trade / supply chain stress`
- `Market instability`
- `Middle East tension`
- `US political uncertainty`
- `China / Taiwan strategic pressure`

---

## B. Free-text Fields

These are open-ended or natural-language fields. Dictionary-only translation is not sufficient for high quality. For now, English fallback is allowed when translated text is unavailable.

### B1. Summary / Explanation Fields
- `daily_summary`
- `summary`
- `headline`
- `decision_line`
- `interpretation`
- `why_it_matters`

### B2. Prediction Narrative Fields
- `prediction_statement`
- `primary_narrative`
- `drivers[].text`
- `monitoring_priorities[].text`
- `expected_outcomes[].text`
- `historical_context.summary`

### B3. Scenario / Explanation Body Fields
- `scenario summary`
- `scenario explanation body`
- `must_not_mean`
- `invalidation`
- `runtime_notes`
- `history summary`

### B4. News Content Fields
- `cards[].title`
- `cards[].summary`
- `articles[].title`
- `articles[].summary`
- `world_view.sections[].cards[].title`
- `world_view.sections[].cards[].summary`

### B5. Digest / Overlay Long-form Text
- `digest.summary`
- `digest.highlights.explanation`
- `overlay controls reason text`
- `overlay note text`

---

## Policy

### Dictionary-based Fields
- Must have `*_i18n`
- Must be translated in analysis / scripts
- UI must not infer, translate, or reconstruct them
- Missing `ja` / `th` may temporarily fall back to `en`, but fallback selection must be resolved through shared i18n helpers and prebuilt fields, not ad hoc page logic

### Free-text Fields
- `*_i18n` is desirable but may be incomplete during the transition period
- English fallback is allowed for missing `ja` / `th`
- UI must not machine-translate or dictionary-assemble free text
- Future local LLM translation may be introduced only on the analysis side

---

## Recommended Implementation Order

### Phase 1
Dictionary-based fields first.

Priority:
1. `global_risk`, `risk`, `status`, `action_bias`, `dominant_scenario`
2. `economic_signals`, `geopolitical_signals`
3. `category`, `label`, `section title`, `sentiment_label`
4. fixed vocabulary used across digest / overlay / prediction / history

### Phase 2
Short free-text fields with controlled scope.

Priority:
1. `daily_summary`
2. `headline`
3. `decision_line`
4. `summary`

### Phase 3
High-volume news content.

Priority:
1. article `title`
2. article `summary`
3. digest article text
4. world view card text

---

## Future Direction

- Dictionary remains the primary stability layer
- Free-text translation may later use local LLM
- Any future translation engine must write results into analysis-side `*_i18n` fields
- UI must remain display-only regardless of translation strategy

---

## Recommended Save Location

This file should be stored at:

`docs/active/i18n_data_classification.md`

Reason:
- `docs/active` is the correct place for current working design and implementation guidance
- This document is a live implementation baseline, not merely a historical reference
