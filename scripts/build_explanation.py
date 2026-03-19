#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
build_explanation.py

Generate explanation artifacts (Prediction Layer Phase4)

Rules:

* Explanation is structured (NOT free text generation)
* Multi-language (en / ja / th)
* Short and bounded (max 3 items)
* UI must not compute anything
  """

import json
import os
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(**file**), ".."))
ANALYSIS_DIR = os.path.join(ROOT, "analysis")

PREDICTION_PATH = os.path.join(ANALYSIS_DIR, "prediction", "prediction_latest.json")
SCENARIO_PATH = os.path.join(ANALYSIS_DIR, "prediction", "scenario_latest.json")
SIGNAL_PATH = os.path.join(ANALYSIS_DIR, "prediction", "signal_latest.json")

OUTPUT_PATH = os.path.join(ANALYSIS_DIR, "explanation", "prediction_explanation_latest.json")

def load_json(path):
if not os.path.exists(path):
return None
with open(path, "r", encoding="utf-8") as f:
return json.load(f)

def safe_list(x):
if isinstance(x, list):
return x
return []

def limit3(lst):
return lst[:3]

def build_summary(pred):
dom = pred.get("dominant_scenario", "unknown")
conf = pred.get("confidence", 0)

```
en = f"{dom} scenario remains dominant with moderate confidence."
ja = f"{dom} シナリオが優勢で、信頼度は中程度。"
th = f"สถานการณ์ {dom} ยังคงเป็นหลัก โดยมีความเชื่อมั่นระดับปานกลาง"

return {"en": en, "ja": ja, "th": th}
```

def build_reasoning(pred, signal):
reasons = []

```
if signal:
    if signal.get("risk_level"):
        reasons.append("Risk level remains elevated.")
    if signal.get("volatility"):
        reasons.append("Volatility conditions persist.")
    if signal.get("trend_strength"):
        reasons.append("Trend signals remain consistent.")

if not reasons:
    reasons = ["No strong contradictory signals detected."]

return {
    "en": limit3(reasons),
    "ja": limit3([translate_ja(r) for r in reasons]),
    "th": limit3([translate_th(r) for r in reasons]),
}
```

def build_drivers(pred):
drivers = safe_list(pred.get("drivers", []))
if not drivers:
drivers = ["Scenario alignment", "Signal consistency"]

```
return {
    "en": limit3(drivers),
    "ja": limit3([translate_ja(d) for d in drivers]),
    "th": limit3([translate_th(d) for d in drivers]),
}
```

def build_watchpoints(pred):
wp = safe_list(pred.get("watchpoints", []))
if not wp:
wp = ["Signal reversal", "Confidence drop"]

```
return {
    "en": limit3(wp),
    "ja": limit3([translate_ja(w) for w in wp]),
    "th": limit3([translate_th(w) for w in wp]),
}
```

def build_must_not_mean():
base = [
"This is not a guaranteed outcome.",
"Confidence is not accuracy.",
"Watchpoints are not confirmed events."
]

```
return {
    "en": base,
    "ja": limit3([translate_ja(x) for x in base]),
    "th": limit3([translate_th(x) for x in base]),
}
```

# --- simple translation stubs (replace later with proper system) ---

def translate_ja(text):
mapping = {
"Risk level remains elevated.": "リスク水準は依然として高い。",
"Volatility conditions persist.": "ボラティリティが継続している。",
"Trend signals remain consistent.": "トレンドシグナルは一貫している。",
"No strong contradictory signals detected.": "強い逆方向シグナルは検出されていない。",
"Scenario alignment": "シナリオ整合性",
"Signal consistency": "シグナルの一貫性",
"Signal reversal": "シグナル反転",
"Confidence drop": "信頼度低下",
"This is not a guaranteed outcome.": "これは確定結果ではない。",
"Confidence is not accuracy.": "信頼度は的中率ではない。",
"Watchpoints are not confirmed events.": "監視点は確定イベントではない。"
}
return mapping.get(text, text)

def translate_th(text):
mapping = {
"Risk level remains elevated.": "ระดับความเสี่ยงยังคงสูง",
"Volatility conditions persist.": "ความผันผวนยังคงอยู่",
"Trend signals remain consistent.": "สัญญาณแนวโน้มยังคงสม่ำเสมอ",
"No strong contradictory signals detected.": "ไม่พบสัญญาณขัดแย้งที่ชัดเจน",
"Scenario alignment": "ความสอดคล้องของสถานการณ์",
"Signal consistency": "ความสม่ำเสมอของสัญญาณ",
"Signal reversal": "การกลับทิศของสัญญาณ",
"Confidence drop": "ความเชื่อมั่นลดลง",
"This is not a guaranteed outcome.": "นี่ไม่ใช่ผลลัพธ์ที่รับประกัน",
"Confidence is not accuracy.": "ความเชื่อมั่นไม่ใช่ความแม่นยำ",
"Watchpoints are not confirmed events.": "จุดเฝ้าระวังไม่ใช่เหตุการณ์ที่ยืนยันแล้ว"
}
return mapping.get(text, text)

def build():
pred = load_json(PREDICTION_PATH)
scen = load_json(SCENARIO_PATH)
sig = load_json(SIGNAL_PATH)

```
if not pred:
    return

explanation = {
    "as_of": datetime.utcnow().strftime("%Y-%m-%d"),
    "subject": "prediction",
    "status": "ok",
    "lang_default": "en",
    "languages": ["en", "ja", "th"],

    "explanation": {
        "summary": build_summary(pred),
        "reasoning": build_reasoning(pred, sig),
        "drivers": build_drivers(pred),
        "watchpoints": build_watchpoints(pred),
        "must_not_mean": build_must_not_mean(),
    },

    "based_on": [
        "prediction_latest.json",
        "scenario_latest.json",
        "signal_latest.json"
    ]
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(explanation, f, ensure_ascii=False, indent=2)

print("[OK] wrote", OUTPUT_PATH)
```

if **name** == "**main**":
build()
