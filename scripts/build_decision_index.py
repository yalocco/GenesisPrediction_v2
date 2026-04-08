#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional


ROOT_MARKER = "# Decision Log (GenesisPrediction v2)"
INDEX_HEADER = """# Decision Index (GenesisPrediction v2)

Status: Active
Purpose: decision_log の検索効率を向上させるための軽量インデックス
Last Updated: {last_updated}

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
"""

INDEX_FOOTER = """
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
"""

# One-time curated core entries.
# These are stable, high-priority rules that do not always carry explicit dated headings
# in decision_log.md, so we keep them deterministic here.
CORE_ENTRIES: List[Dict[str, str]] = [
    {
        "date": "CORE",
        "title": "Analysis Is Single Source of Truth",
        "tags": "analysis, ssot, architecture",
        "rule": "analysis is the single source of truth and ui must not override it",
    },
    {
        "date": "CORE",
        "title": "UI Is Display Only",
        "tags": "ui, display_only, architecture",
        "rule": "ui must not compute, decide, translate, or generate meaning",
    },
    {
        "date": "CORE",
        "title": "Full File Delivery Only",
        "tags": "generation, full_file, integrity",
        "rule": "diff proposals are prohibited and full files are required",
    },
    {
        "date": "CORE",
        "title": "Existing File Must Be Verified",
        "tags": "generation, integrity, verification",
        "rule": "do not generate from guesswork when an existing file has not been verified",
    },
    {
        "date": "CORE",
        "title": "Vector Memory Is Reference Only",
        "tags": "vector_memory, reference, architecture",
        "rule": "vector memory must be reference-only and must not overwrite analysis",
    },
]

TITLE_TAG_HINTS = {
    "decision action hardening": "prediction, decision_actions, scenario, triggers, outcomes",
    "explanation is a mirror of prediction": "explanation, prediction, mirror",
    "watchpoints must not be mixed across layers": "watchpoints, prediction, explanation",
    "deploy hardening": "deploy, target_only, permission, hardening",
    "full file integrity reinforcement": "file_integrity, copy_safety, rules",
    "deploy verification must follow deploy": "deploy, verify, operations",
    "morning ritual end-to-end chain is valid": "operations, ritual, deploy, verify",
    "prediction enhancement phase 2 completion": "prediction, recall, quality",
    "dirty repo guard enforcement": "git, operations, run_guard",
    "pre-run commit rule": "git, operations, commit",
    "powershell switch parameter rule": "powershell, scripts, rules",
    "scenario engine must produce causal branches, not templates": "scenario, causal, branch, watchpoints",
    "scenario drivers must be cause-oriented": "scenario, drivers, cause",
    "prediction must be decision-grade, not scenario restatement": "prediction, decision, architecture, scenario",
    "prediction drivers must be limited and cause-oriented": "prediction, drivers, cause",
    "prediction monitoring priorities must follow branch logic": "prediction, monitoring, branch_logic",
    "explanation must be mirror-only across structured fields": "explanation, mirror, structure",
    "explanation may clarify reading, but must not create new truth": "explanation, mirror, truth",
    "scenario driver canonicalization must exclude scenario labels": "scenario, drivers, canonicalization",
    "prediction enhancement (cause-oriented scenario + decision-grade prediction) is completed": "prediction, scenario, milestone",
    "scenario transmission must be deterministic per branch": "scenario, transmission, deterministic, branch",
    "scenario narrative must be built from structured drivers, not raw tags": "scenario, narrative, drivers",
    "scenario narrative outcomes must align with branch outcomes": "scenario, narrative, outcomes, branch",
    "internal scenario / transmission tokens must be snake case": "scenario, tokens, snake_case, i18n",
    "scenario must carry invalidation conditions": "scenario, invalidation, monitoring",
    "scenario engine final polish completed": "scenario, production_ready, milestone",
    "markdown editing must use download-based full file workflow": "markdown, workflow, download, integrity",
    "prediction output must preserve structure (no partial translation)": "prediction, i18n, translation, structure",
    "scenario labels must not use generic translation": "scenario, i18n, labels",
    "prediction enhancement v4 completed": "prediction, milestone, v4",
    "prediction layer i18n must be fully resolved in analysis (structure fix)": "prediction, i18n, analysis",
    "prediction must carry structured semantics (no meaning gap)": "prediction, structure, explanation, ui",
    "system completion and phase transition to operation": "operations, completion, ritual",
    "prediction history must be synced to data layer for ui": "history, data_layer, ui",
    "local server and distribution structure must be strictly distinguished": "distribution, local_server, ui",
    "ui 404 debug must start from distribution layer": "ui, debug, distribution",
    "gui final audit completed": "ui, audit, stability",
    "pre-deploy payload freshness check is mandatory": "deploy, payload, freshness",
    "en as ssot (language architecture finalization)": "i18n, language, ssot",
    "explanation pure mirror hardening": "explanation, mirror, hardening",
    "structured truth consolidation": "prediction, structure, truth",
    "prediction enhancement phase1": "prediction, enhancement, phase1",
}

STOP_HEADINGS = {
    "# ",
    "## ",
    "### ",
}


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def slugify_title(title: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip().lower())
    return re.sub(r"_+", "_", text).strip("_")


def title_to_tags(title: str) -> str:
    key = title.strip().lower()
    if key in TITLE_TAG_HINTS:
        return TITLE_TAG_HINTS[key]

    words = [w for w in re.split(r"[^a-zA-Z0-9]+", key) if w]
    words = [w for w in words if w not in {"the", "is", "must", "be", "to", "and", "of", "in", "for", "from", "with"}]
    return ", ".join(words[:5]) if words else "decision"


def extract_last_updated(text: str) -> str:
    m = re.search(r"Last Updated:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
    return m.group(1) if m else "unknown"


def extract_rule(block: str) -> str:
    code_blocks = re.findall(r"```text\s*(.*?)```", block, flags=re.DOTALL)
    for code in code_blocks:
        lines = [normalize_space(line) for line in code.splitlines() if normalize_space(line)]
        if not lines:
            continue
        first = lines[0]
        first = first.rstrip("。.")
        return first.lower()

    lines = []
    for raw in block.splitlines():
        s = normalize_space(raw)
        if not s:
            continue
        if s.startswith("対象"):
            continue
        if s.startswith("理由"):
            continue
        if s.startswith("補足"):
            continue
        if s.startswith("Status:"):
            continue
        if s.startswith("```"):
            continue
        lines.append(s)

    if lines:
        return lines[0].rstrip("。.").lower()

    return "rule not extracted"


def split_dated_entries(text: str) -> List[Dict[str, str]]:
    lines = text.splitlines()
    results: List[Dict[str, str]] = []

    i = 0
    current_date: Optional[str] = None

    while i < len(lines):
        line = lines[i].strip()

        date_match = re.match(r"^##\s+([0-9]{4}-[0-9]{2}-[0-9]{2})$", line)
        if date_match:
            current_date = date_match.group(1)
            i += 1
            continue

        title_match = re.match(r"^###\s+(.+?)\s*$", line)
        if current_date and title_match:
            title = normalize_space(title_match.group(1))
            block_lines: List[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                stripped = nxt.strip()
                if re.match(r"^##\s+[0-9]{4}-[0-9]{2}-[0-9]{2}$", stripped):
                    break
                if re.match(r"^###\s+.+$", stripped):
                    break
                block_lines.append(nxt)
                i += 1

            block = "\n".join(block_lines)
            results.append(
                {
                    "date": current_date,
                    "title": title,
                    "tags": title_to_tags(title),
                    "rule": extract_rule(block),
                }
            )
            continue

        i += 1

    return results


def dedupe_entries(entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    output = []
    for item in entries:
        key = (item["date"].strip(), item["title"].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def render_entry(entry: Dict[str, str]) -> str:
    return f"""---

## {entry['date']} | {entry['title']}

tags: {entry['tags']}

rule: {entry['rule']}

source: docs/core/decision_log.md
"""


def build_index_text(decision_log_text: str) -> str:
    if ROOT_MARKER not in decision_log_text:
        raise ValueError("input does not look like decision_log.md")

    last_updated = extract_last_updated(decision_log_text)
    dated_entries = split_dated_entries(decision_log_text)
    entries = dedupe_entries(CORE_ENTRIES + dated_entries)

    parts = [INDEX_HEADER.format(last_updated=last_updated)]
    parts.extend(render_entry(entry) for entry in entries)
    parts.append(INDEX_FOOTER.lstrip("\n"))
    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate decision_index.md from decision_log.md")
    parser.add_argument(
        "--input",
        default="docs/core/decision_log.md",
        help="Path to decision_log.md",
    )
    parser.add_argument(
        "--output",
        default="docs/core/decision_index.md",
        help="Path to write decision_index.md",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    text = input_path.read_text(encoding="utf-8")
    index_text = build_index_text(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(index_text, encoding="utf-8")

    print(f"[build_decision_index] wrote {output_path}")


if __name__ == "__main__":
    main()
