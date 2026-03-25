# GenesisPrediction i18n Dictionary Template

## Recommended path
`config/i18n/i18n_dictionary.json`

## Purpose
A controlled vocabulary dictionary for analysis-side multilingual expansion.

## Rules
- UI must not translate.
- Analysis/scripts resolve dictionary-based `*_i18n`.
- Free-text fields may fallback to English.
- Do not store article titles or long summaries here.

## Suggested next step
1. Save `i18n_dictionary_template.json` as `config/i18n/i18n_dictionary.json`
2. Add a small helper such as `scripts/lib/i18n_dictionary.py`
3. Apply it first to:
   - build_world_view_model_latest.py
   - build_digest_view_model.py
   - explanation builders for short labels only
