from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime


ANALYSIS_DIR = Path("data/world_politics/analysis")
OBS_MD = Path("docs/observation.md")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _normalize_date(s: str) -> str | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%d")
    except Exception:
        return s


def _find_daily_summary(date_str: str | None) -> Path | None:
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    if not files:
        return None
    if date_str:
        p = ANALYSIS_DIR / f"daily_summary_{date_str}.json"
        if p.exists():
            return p
    return max(files, key=lambda p: p.stat().st_mtime)


def _md_escape(s: str) -> str:
    # 最低限（必要なら増やす）
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _render_section(doc: dict) -> tuple[str, str]:
    """
    Returns (date_str, markdown_section_with_markers)
    """
    meta = doc.get("meta") or {}
    date_str = _normalize_date(meta.get("date") or "")
    if not date_str:
        # ファイル名日付に頼りたいが、ここは必ずある前提で運用しているので fallback
        date_str = "unknown-date"

    marker_start = f"<!-- OBS:{date_str} -->"
    marker_end = f"<!-- /OBS:{date_str} -->"

    # confidence info
    conf_key = "confidence_of_hypotheses" if doc.get("confidence_of_hypotheses") is not None else "confidence"
    conf = _safe_float(doc.get(conf_key))
    base = _safe_float(doc.get("confidence_analog_base"))
    delta = _safe_float(doc.get("confidence_analog_delta"), 0.0)
    reason = str(doc.get("confidence_analog_reason") or "").strip()

    # analogs
    analogs = doc.get("historical_analogs") or []
    analog_tags = doc.get("historical_analog_tags") or []

    lines: list[str] = []
    lines.append(marker_start)
    lines.append(f"## {date_str}")
    lines.append("")
    lines.append("### Historical analogs")
    if analog_tags:
        lines.append(f"- tags: `{', '.join(map(str, analog_tags))}`")
    else:
        lines.append("- tags: (none)")
    lines.append("")

    # confidence block
    if conf is None:
        lines.append("### Confidence")
        lines.append("- confidence: (none)")
    else:
        lines.append("### Confidence")
        # base が無い日もあるので分岐
        if base is None:
            lines.append(f"- {conf_key}: **{conf:.4f}**")
        else:
            lines.append(f"- {conf_key}: **{conf:.4f}**  (base {base:.4f} + delta {delta:+.3f})")
        if reason:
            lines.append(f"- reason: {reason}")
    lines.append("")

    # analog list
    if not analogs:
        lines.append("### Top analogs (0)")
        lines.append("- (none)")
        lines.append("")
    else:
        lines.append(f"### Top analogs ({min(3, len(analogs))})")
        lines.append("")
        for i, a in enumerate(analogs[:3], 1):
            title = str(a.get("title") or a.get("name") or f"Analog {i}")
            score = _safe_float(a.get("score"))
            matched = a.get("matched_tags") or a.get("matched") or []
            summary = str(a.get("summary") or "").strip()
            notes = str(a.get("notes") or "").strip()

            lines.append(f"#### {i}. {title}")
            if score is None:
                lines.append("- score: (none)")
            else:
                lines.append(f"- score: **{score:.4f}**")
            if matched:
                lines.append(f"- matched_tags: `{', '.join(map(str, matched))}`")
            else:
                lines.append("- matched_tags: (none)")

            if summary:
                lines.append("")
                lines.append("**Summary**")
                lines.append("")
                lines.append(_md_escape(summary))
            if notes:
                lines.append("")
                lines.append("<details>")
                lines.append("<summary>Notes</summary>")
                lines.append("")
                lines.append(_md_escape(notes))
                lines.append("")
                lines.append("</details>")
            lines.append("")

    lines.append(marker_end)
    lines.append("")
    return date_str, "\n".join(lines)


def _upsert_section(md_text: str, date_str: str, new_section: str) -> str:
    """
    If section markers exist, replace.
    Else append to end.
    """
    start = f"<!-- OBS:{date_str} -->"
    end = f"<!-- /OBS:{date_str} -->"

    if start in md_text and end in md_text:
        pre = md_text.split(start)[0]
        post = md_text.split(end, 1)[1]  # end marker以降
        # pre の末尾改行整理
        pre = pre.rstrip() + "\n\n"
        post = post.lstrip()
        return pre + new_section + post

    # append
    md_text = md_text.rstrip() + "\n\n"
    return md_text + new_section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="", help="YYYY-MM-DD (optional). If missing, use latest daily_summary.")
    args = parser.parse_args()

    date_str = args.date.strip() or None
    target = _find_daily_summary(date_str)
    if not target:
        print("[WARN] no daily_summary_*.json found")
        return

    doc = _read_json(target)
    date_str2, section = _render_section(doc)

    # ensure docs dir
    OBS_MD.parent.mkdir(parents=True, exist_ok=True)

    if OBS_MD.exists():
        old = OBS_MD.read_text(encoding="utf-8")
    else:
        old = "# Observation Log\n\n(autogenerated sections below)\n\n"

    new = _upsert_section(old, date_str2, section)
    OBS_MD.write_text(new, encoding="utf-8")

    print(f"[OK] upserted {OBS_MD} for {date_str2} (source: {target.name})")


if __name__ == "__main__":
    main()
