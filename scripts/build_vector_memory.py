from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from qdrant_client import QdrantClient
from qdrant_client.http import models


DEFAULT_COLLECTION = "genesis_reference_memory"
DEFAULT_EMBEDDING_MODEL = os.getenv("VM_EMBEDDING_MODEL", "BAAI/bge-small-en")
DEFAULT_BATCH_SIZE = 32
MAX_DOC_CHARS = 3500
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

VECTOR_MEMORY_BUILD_LATEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "analysis"
    / "prediction"
    / "vector_memory_build_latest.json"
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
DECISION_HEADING_RE = re.compile(r"^##\s+Decision:\s+(.*)$", re.MULTILINE)
DATE_DIR_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(slots=True)
class MemoryItem:
    point_id: int
    document: str
    payload: dict[str, Any]


@dataclass(slots=True)
class BuildStats:
    decision_log: int = 0
    prediction_snapshot: int = 0
    scenario_snapshot: int = 0
    signal_snapshot: int = 0
    historical_pattern: int = 0
    historical_analog: int = 0
    explanation: int = 0
    skipped: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "decision_log": self.decision_log,
            "prediction_snapshot": self.prediction_snapshot,
            "scenario_snapshot": self.scenario_snapshot,
            "signal_snapshot": self.signal_snapshot,
            "historical_pattern": self.historical_pattern,
            "historical_analog": self.historical_analog,
            "explanation": self.explanation,
            "skipped": self.skipped,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build GenesisPrediction Vector Memory in Qdrant."
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path.",
    )
    parser.add_argument(
        "--qdrant-url",
        default=DEFAULT_QDRANT_URL,
        help="Qdrant URL, for example http://localhost:6333",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Qdrant collection name.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="FastEmbed text model name supported by qdrant-client[fastembed].",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Embedding/upload batch size.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the collection before indexing.",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip analysis/prediction/history indexing.",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clip_text(text: str, limit: int = MAX_DOC_CHARS) -> str:
    text = normalize_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def stable_point_id(memory_id: str) -> int:
    digest = hashlib.md5(memory_id.encode("utf-8")).hexdigest()[:16]
    return int(digest, 16)


def stable_memory_id(*parts: str) -> str:
    raw = "::".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def rel_path_str(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def ensure_lang_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for lang in SUPPORTED_LANGUAGES:
        text = value.get(lang)
        if text is None:
            continue
        text_str = str(text).strip()
        if text_str:
            out[lang] = text_str
    return out


def finalize_text_i18n(base_en: str, partial: dict[str, str]) -> dict[str, str]:
    en_text = str(partial.get("en") or base_en or "").strip()
    ja_text = str(partial.get("ja") or en_text).strip()
    th_text = str(partial.get("th") or en_text).strip()
    return {
        "en": en_text,
        "ja": ja_text,
        "th": th_text,
    }


def choose_i18n_text_map(data: dict[str, Any], base_key: str) -> dict[str, str]:
    base_text = str(data.get(base_key) or "").strip()
    partial = ensure_lang_map(data.get(f"{base_key}_i18n"))
    return finalize_text_i18n(base_text, partial)


def preferred_lang_text(i18n_map: dict[str, str], fallback: str = "") -> str:
    return (
        str(i18n_map.get(LANG_DEFAULT) or "").strip()
        or str(i18n_map.get("en") or "").strip()
        or fallback
    )


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def normalize_tag(value: str) -> str:
    clean = re.sub(r"\s+", "_", value.strip().lower())
    clean = re.sub(r"[^a-z0-9_\-:/]+", "", clean)
    return clean.strip("_")


def extract_markdown_sections(text: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        stripped = normalize_text(text)
        return [("document", stripped)] if stripped else []

    sections: list[tuple[str, str]] = []
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append(("document", normalize_text(preamble)))

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = normalize_text(text[start:end])
        if body:
            sections.append((title, body))
    return sections


def extract_decision_log_chunks(text: str) -> list[tuple[str, str, str]]:
    """
    Returns structured chunks as:
    (chunk_kind, title, body)

    chunk_kind:
      - document_purpose
      - decision
      - section
    """
    chunks: list[tuple[str, str, str]] = []
    decision_matches = list(DECISION_HEADING_RE.finditer(text))
    if decision_matches:
        purpose_sections = extract_markdown_sections(text[: decision_matches[0].start()])
        for title, body in purpose_sections:
            if body:
                chunks.append(("document_purpose", title, body))

        for i, match in enumerate(decision_matches):
            title = match.group(1).strip()
            start = match.end()
            end = decision_matches[i + 1].start() if i + 1 < len(decision_matches) else len(text)
            body = normalize_text(text[start:end])
            if body:
                chunks.append(("decision", title, body))
        return chunks

    for title, body in extract_markdown_sections(text):
        chunks.append(("section", title, body))
    return chunks


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    embedding_model: str,
    recreate: bool,
) -> None:
    if recreate and client.collection_exists(collection_name):
        client.delete_collection(collection_name=collection_name)

    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=client.get_fastembed_vector_params(),
        optimizers_config=models.OptimizersConfigDiff(indexing_threshold=0),
    )

    _ = client.get_embedding_size(embedding_model)


def add_items(
    client: QdrantClient,
    collection_name: str,
    items: list[MemoryItem],
    batch_size: int,
) -> None:
    if not items:
        return

    documents = [item.document for item in items]
    metadata = [item.payload for item in items]
    ids = [item.point_id for item in items]
    client.add(
        collection_name=collection_name,
        documents=documents,
        metadata=metadata,
        ids=ids,
        batch_size=batch_size,
    )


def title_i18n_from_markdown_title(title: str) -> dict[str, str]:
    clean = normalize_text(title)
    return {
        "en": clean,
        "ja": clean,
        "th": clean,
    }


def summary_i18n_from_markdown_body(body: str) -> dict[str, str]:
    clean = clip_text(body, 800)
    return {
        "en": clean,
        "ja": clean,
        "th": clean,
    }


def build_decision_log_items(root: Path, stats: BuildStats) -> list[MemoryItem]:
    path = root / "docs" / "core" / "decision_log.md"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    chunks = extract_decision_log_chunks(text)
    items: list[MemoryItem] = []

    for chunk_kind, title, body in chunks:
        title_i18n = title_i18n_from_markdown_title(title)
        summary_i18n = summary_i18n_from_markdown_body(body)
        memory_id = stable_memory_id(
            "decision_log",
            rel_path_str(path, root),
            chunk_kind,
            title,
        )
        payload = {
            "memory_id": memory_id,
            "memory_type": "decision_log",
            "lang_default": LANG_DEFAULT,
            "languages": list(SUPPORTED_LANGUAGES),
            "as_of": extract_as_of_from_text(title, body),
            "title": preferred_lang_text(title_i18n, title),
            "title_i18n": title_i18n,
            "summary": preferred_lang_text(summary_i18n, clip_text(body, 800)),
            "summary_i18n": summary_i18n,
            "tags": derive_tags_from_text(
                title + "\n" + body,
                base=["decision_log", "docs", chunk_kind],
            ),
            "source_path": rel_path_str(path, root),
            "source_kind": "docs",
            "chunk_kind": chunk_kind,
            "chunk_title": title,
            "version": "v1",
            "indexed_at": utc_now_iso(),
        }
        document = build_decision_log_document(chunk_kind=chunk_kind, title=title, body=body)
        items.append(MemoryItem(stable_point_id(memory_id), clip_text(document), payload))
        stats.decision_log += 1

    return items


def build_decision_log_document(*, chunk_kind: str, title: str, body: str) -> str:
    lines = [
        f"memory_type: decision_log",
        f"chunk_kind: {chunk_kind}",
        f"title: {title}",
    ]
    if chunk_kind == "decision":
        lines.append(f"decision: {title}")
    lines.append("")
    lines.append(body)
    return "\n".join(lines)


def build_prediction_history_items(root: Path, stats: BuildStats) -> list[MemoryItem]:
    history_root = root / "analysis" / "prediction" / "history"
    if not history_root.exists():
        return []

    items: list[MemoryItem] = []
    for dated_dir in sorted(history_root.iterdir()):
        if not dated_dir.is_dir() or not DATE_DIR_RE.fullmatch(dated_dir.name):
            continue
        as_of = dated_dir.name
        for file_name, memory_type in (
            ("prediction.json", "prediction_snapshot"),
            ("scenario.json", "scenario_snapshot"),
            ("signal.json", "signal_snapshot"),
            ("historical_pattern.json", "historical_pattern"),
            ("historical_analog.json", "historical_analog"),
        ):
            path = dated_dir / file_name
            if not path.exists():
                continue
            item = build_json_artifact_item(root, path, memory_type, as_of=as_of)
            if item is None:
                stats.skipped += 1
                continue
            items.append(item)
            increment_stats(stats, memory_type)
    return items


def build_historical_library_items(root: Path, stats: BuildStats) -> list[MemoryItem]:
    historical_root = root / "analysis" / "historical"
    if not historical_root.exists():
        return []

    items: list[MemoryItem] = []
    for path in sorted(historical_root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            stats.skipped += 1
            continue

        patterns = extract_patterns_from_library(data)
        for index, pattern in enumerate(patterns):
            memory_type = infer_historical_memory_type(pattern)
            pattern_id = str(
                pattern.get("pattern_id")
                or pattern.get("analog_id")
                or f"item-{index}"
            )
            title_map = choose_i18n_text_map(pattern, "name")
            if not any(title_map.values()):
                fallback_title = str(pattern.get("name") or pattern.get("title") or pattern_id)
                title_map = finalize_text_i18n(fallback_title, {})
            summary_map = choose_i18n_text_map(pattern, "summary")
            if not any(summary_map.values()):
                fallback_summary = build_summary_from_mapping(pattern, prefer_lang="en")
                summary_map = finalize_text_i18n(fallback_summary, {})
            memory_id = stable_memory_id(memory_type, rel_path_str(path, root), pattern_id)
            payload = {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "lang_default": LANG_DEFAULT,
                "languages": list(SUPPORTED_LANGUAGES),
                "as_of": "static",
                "title": preferred_lang_text(
                    title_map,
                    str(pattern.get("name") or pattern.get("title") or pattern_id),
                ),
                "title_i18n": title_map,
                "summary": preferred_lang_text(
                    summary_map,
                    build_summary_from_mapping(pattern, prefer_lang=LANG_DEFAULT),
                ),
                "summary_i18n": summary_map,
                "tags": derive_tags_from_mapping(pattern, base=["historical", path.stem, memory_type]),
                "source_path": rel_path_str(path, root),
                "source_kind": "analysis",
                "pattern_id": str(pattern.get("pattern_id") or ""),
                "analog_id": str(pattern.get("analog_id") or ""),
                "category": str(pattern.get("category") or path.stem),
                "watchpoints": extract_str_list(pattern, "watchpoints"),
                "cause_tags": extract_str_list(pattern, "cause_tags"),
                "trigger_tags": extract_str_list(pattern, "trigger_tags"),
                "version": str(pattern.get("schema_version", "v1")),
                "indexed_at": utc_now_iso(),
            }
            document = build_historical_document(title_map, pattern, memory_type=memory_type)
            items.append(MemoryItem(stable_point_id(memory_id), clip_text(document), payload))
            increment_stats(stats, memory_type)
    return items


def infer_historical_memory_type(pattern: dict[str, Any]) -> str:
    if pattern.get("analog_id") and not pattern.get("pattern_id"):
        return "historical_analog"
    if pattern.get("analog_examples") and not pattern.get("pattern_id"):
        return "historical_analog"
    return "historical_pattern"


def build_explanation_items(root: Path, stats: BuildStats) -> list[MemoryItem]:
    explanation_root = root / "analysis" / "explanation"
    if not explanation_root.exists():
        return []

    items: list[MemoryItem] = []
    for path in sorted(explanation_root.glob("*.json")):
        item = build_json_artifact_item(
            root,
            path,
            "explanation",
            as_of=extract_as_of_from_json(path),
        )
        if item is None:
            stats.skipped += 1
            continue
        items.append(item)
        stats.explanation += 1
    return items


def build_json_artifact_item(
    root: Path,
    path: Path,
    memory_type: str,
    as_of: str | None,
) -> MemoryItem | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    title_i18n = infer_title_i18n_from_json(path, data, memory_type)
    summary_i18n = infer_summary_i18n_from_json(data)
    title = preferred_lang_text(title_i18n, infer_title_from_json(path, data, memory_type))
    summary = preferred_lang_text(summary_i18n, build_summary_from_mapping(data, prefer_lang=LANG_DEFAULT))
    as_of_value = as_of or str(data.get("as_of", "unknown"))

    memory_id = stable_memory_id(memory_type, rel_path_str(path, root), str(as_of_value), title)
    payload = {
        "memory_id": memory_id,
        "memory_type": memory_type,
        "lang_default": str(data.get("lang_default") or LANG_DEFAULT).strip() or LANG_DEFAULT,
        "languages": data.get("languages") if isinstance(data.get("languages"), list) else list(SUPPORTED_LANGUAGES),
        "as_of": as_of_value,
        "title": title,
        "title_i18n": title_i18n,
        "summary": clip_text(summary, 800),
        "summary_i18n": {
            lang: clip_text(text, 800)
            for lang, text in summary_i18n.items()
        },
        "tags": derive_tags_from_mapping(data, base=[memory_type]),
        "source_path": rel_path_str(path, root),
        "source_kind": "analysis",
        "version": str(data.get("engine_version", data.get("schema_version", "v1"))),
        "indexed_at": utc_now_iso(),
    }
    payload.update(extract_memory_specific_fields(data, memory_type))
    document = build_json_document(title_i18n, data, memory_type=memory_type)
    return MemoryItem(stable_point_id(memory_id), clip_text(document), payload)


def infer_title_from_json(path: Path, data: dict[str, Any], memory_type: str) -> str:
    for key in ("title", "headline", "dominant_pattern", "dominant_analog", "dominant_scenario"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{memory_type}:{path.stem}"


def infer_title_i18n_from_json(path: Path, data: dict[str, Any], memory_type: str) -> dict[str, str]:
    for key in ("title", "headline", "dominant_pattern", "dominant_analog", "dominant_scenario"):
        i18n = ensure_lang_map(data.get(f"{key}_i18n"))
        value = data.get(key)
        if i18n or (isinstance(value, str) and value.strip()):
            return finalize_text_i18n(str(value or "").strip(), i18n)
    fallback = f"{memory_type}:{path.stem}"
    return finalize_text_i18n(fallback, {})


def infer_summary_i18n_from_json(data: dict[str, Any]) -> dict[str, str]:
    candidates = [
        "summary",
        "headline",
        "why_it_matters",
        "prediction_statement",
        "primary_narrative",
        "decision_line",
        "interpretation",
    ]
    for key in candidates:
        i18n = ensure_lang_map(data.get(f"{key}_i18n"))
        value = data.get(key)
        if i18n or (isinstance(value, str) and value.strip()):
            return finalize_text_i18n(str(value or "").strip(), i18n)

    return {
        "en": build_summary_from_mapping(data, prefer_lang="en"),
        "ja": build_summary_from_mapping(data, prefer_lang="ja"),
        "th": build_summary_from_mapping(data, prefer_lang="th"),
    }


def extract_as_of_from_json(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "unknown"
    value = data.get("as_of")
    if isinstance(value, str) and value.strip():
        return value.strip()
    match = DATE_DIR_RE.search(path.as_posix())
    return match.group(0) if match else "unknown"


def extract_as_of_from_text(title: str, body: str) -> str:
    combined = f"{title}\n{body}"
    match = re.search(r"20\d{2}-\d{2}(?:-\d{2})?", combined)
    return match.group(0) if match else "unknown"


def extract_str_list(data: dict[str, Any], key: str, *, limit: int = 12) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            clean = item.strip()
        elif isinstance(item, dict):
            clean = normalize_text(item)
        else:
            clean = str(item).strip()
        if clean:
            result.append(clean)
        if len(result) >= limit:
            break
    return result


def extract_scalar(data: dict[str, Any], key: str) -> str | int | float | None:
    value = data.get(key)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (str, int, float)):
        if isinstance(value, str) and not value.strip():
            return None
        return value
    return None


def derive_tags_from_text(text: str, base: list[str] | None = None) -> list[str]:
    tags = list(base or [])
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9_\-/]{2,}", text)
    lowered: list[str] = []
    for item in candidates[:40]:
        value = normalize_tag(item)
        if value and value not in lowered:
            lowered.append(value)
    return dedupe_preserve_order(tags + lowered[:12])


def derive_tags_from_mapping(data: dict[str, Any], base: list[str] | None = None) -> list[str]:
    tags: list[str] = list(base or [])
    for key in (
        "tags",
        "matched_signals",
        "watchpoints",
        "drivers",
        "supporting_signals",
        "cause_tags",
        "trigger_tags",
        "invalidation",
        "invalidation_conditions",
        "expected_outcomes",
    ):
        value = data.get(key)
        if isinstance(value, list):
            for item in value[:10]:
                if isinstance(item, str) and item.strip():
                    normalized = normalize_tag(item)
                    if normalized:
                        tags.append(normalized)
    for key in (
        "overall_risk",
        "dominant_scenario",
        "dominant_pattern",
        "dominant_analog",
        "category",
        "subject",
        "status",
    ):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            normalized = normalize_tag(value)
            if normalized:
                tags.append(normalized)
    return dedupe_preserve_order(tags[:16])


def build_summary_from_mapping(data: dict[str, Any], prefer_lang: str = LANG_DEFAULT) -> str:
    interesting_keys = [
        "summary",
        "headline",
        "why_it_matters",
        "overall_risk",
        "dominant_scenario",
        "confidence",
        "pattern_confidence",
        "analog_confidence",
        "dominant_pattern",
        "dominant_analog",
        "status",
        "subject",
    ]
    parts: list[str] = []
    for key in interesting_keys:
        if key not in data and f"{key}_i18n" not in data:
            continue

        i18n = ensure_lang_map(data.get(f"{key}_i18n"))
        value = (
            str(i18n.get(prefer_lang) or "").strip()
            or str(i18n.get("en") or "").strip()
        )
        if not value:
            raw = data.get(key)
            if raw in (None, "", [], {}):
                continue
            value = normalize_text(raw)

        if value in ("", "[]", "{}"):
            continue
        parts.append(f"{key}={value}")

    if not parts:
        parts.append(normalize_text(data))
    return " | ".join(parts)


def extract_memory_specific_fields(data: dict[str, Any], memory_type: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    scalar_keys = [
        "overall_risk",
        "dominant_scenario",
        "confidence",
        "horizon_days",
        "signal_count",
        "pattern_confidence",
        "analog_confidence",
        "dominant_pattern",
        "dominant_analog",
        "category",
        "subject",
        "status",
    ]
    list_keys = [
        "watchpoints",
        "drivers",
        "invalidation",
        "invalidation_conditions",
        "supporting_signals",
        "matched_signals",
        "expected_outcomes",
        "similarities",
        "differences",
        "historical_outcomes",
        "based_on",
        "must_not_mean",
    ]

    if memory_type in {
        "prediction_snapshot",
        "scenario_snapshot",
        "signal_snapshot",
        "historical_pattern",
        "historical_analog",
        "explanation",
    }:
        for key in scalar_keys:
            value = extract_scalar(data, key)
            if value is not None:
                payload[key] = value
        for key in list_keys:
            values = extract_str_list(data, key)
            if values:
                payload[key] = values

    if memory_type == "scenario_snapshot":
        payload["scenario_probabilities"] = extract_scenario_probabilities(data)
    if memory_type == "prediction_snapshot":
        payload["scenario_probabilities"] = extract_scenario_probabilities(data)
    return payload


def extract_scenario_probabilities(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    direct_keys = ("best_case", "base_case", "worst_case")
    for key in direct_keys:
        value = data.get(key)
        if isinstance(value, (int, float)):
            out[key] = value

    scenarios = data.get("scenarios")
    if isinstance(scenarios, dict):
        for key in direct_keys:
            value = scenarios.get(key)
            if isinstance(value, (int, float)):
                out[key] = value

    return out


def build_json_document(title_i18n: dict[str, str], data: dict[str, Any], *, memory_type: str) -> str:
    lines = [
        f"memory_type: {memory_type}",
        preferred_lang_text(title_i18n, title_i18n.get("en", "")),
        f"title_ja: {title_i18n.get('ja', '')}",
        f"title_en: {title_i18n.get('en', '')}",
        f"title_th: {title_i18n.get('th', '')}",
    ]

    ordered_keys = ordered_document_keys(memory_type)
    seen: set[str] = set()

    for key in ordered_keys:
        if key in data:
            append_document_line(lines, key, data[key])
            seen.add(key)

    for key, value in data.items():
        if key in seen:
            continue
        append_document_line(lines, key, value)

    return "\n".join(lines)


def ordered_document_keys(memory_type: str) -> list[str]:
    common = [
        "as_of",
        "summary",
        "summary_i18n",
        "headline",
        "headline_i18n",
        "why_it_matters",
        "why_it_matters_i18n",
    ]
    if memory_type == "prediction_snapshot":
        return common + [
            "overall_risk",
            "dominant_scenario",
            "confidence",
            "horizon_days",
            "signal_count",
            "drivers",
            "drivers_i18n",
            "watchpoints",
            "watchpoints_i18n",
            "invalidation",
            "invalidation_i18n",
            "expected_outcomes",
            "expected_outcomes_i18n",
            "scenarios",
            "best_case",
            "base_case",
            "worst_case",
        ]
    if memory_type == "scenario_snapshot":
        return common + [
            "dominant_scenario",
            "confidence",
            "drivers",
            "drivers_i18n",
            "watchpoints",
            "watchpoints_i18n",
            "invalidation",
            "invalidation_i18n",
            "supporting_signals",
            "matched_signals",
            "expected_outcomes",
            "expected_outcomes_i18n",
            "scenarios",
            "best_case",
            "base_case",
            "worst_case",
        ]
    if memory_type == "signal_snapshot":
        return common + [
            "overall_risk",
            "supporting_signals",
            "matched_signals",
            "drivers",
            "drivers_i18n",
            "watchpoints",
            "watchpoints_i18n",
            "invalidation",
            "invalidation_i18n",
        ]
    if memory_type in {"historical_pattern", "historical_analog"}:
        return common + [
            "category",
            "dominant_pattern",
            "dominant_analog",
            "pattern_confidence",
            "analog_confidence",
            "cause_tags",
            "trigger_tags",
            "watchpoints",
            "watchpoints_i18n",
            "expected_outcomes",
            "similarities",
            "differences",
            "historical_outcomes",
        ]
    if memory_type == "explanation":
        return common + [
            "subject",
            "status",
            "based_on",
            "drivers",
            "drivers_i18n",
            "watchpoints",
            "watchpoints_i18n",
            "invalidation",
            "invalidation_i18n",
            "must_not_mean",
            "must_not_mean_i18n",
            "ui_terms",
        ]
    return common


def append_document_line(lines: list[str], key: str, value: Any) -> None:
    if value in (None, "", [], {}):
        return
    if key.endswith("_i18n") and isinstance(value, dict):
        ja = value.get("ja")
        en = value.get("en")
        th = value.get("th")
        if isinstance(ja, str) or isinstance(en, str) or isinstance(th, str):
            if ja:
                lines.append(f"{key}.ja: {normalize_text(ja)}")
            if en:
                lines.append(f"{key}.en: {normalize_text(en)}")
            if th:
                lines.append(f"{key}.th: {normalize_text(th)}")
            return
        if isinstance(ja, list) or isinstance(en, list) or isinstance(th, list):
            if ja:
                lines.append(f"{key}.ja: {normalize_text(ja)}")
            if en:
                lines.append(f"{key}.en: {normalize_text(en)}")
            if th:
                lines.append(f"{key}.th: {normalize_text(th)}")
            return
    lines.append(f"{key}: {normalize_text(value)}")


def build_historical_document(title_i18n: dict[str, str], pattern: dict[str, Any], *, memory_type: str) -> str:
    fields = [
        "summary",
        "summary_i18n",
        "cause_tags",
        "trigger_tags",
        "event_chain",
        "impact_chain",
        "economic_outcomes",
        "economic_outcomes_i18n",
        "political_outcomes",
        "civilization_outcomes",
        "watchpoints",
        "watchpoints_i18n",
        "analog_examples",
        "analog_examples_i18n",
        "similarities",
        "differences",
        "historical_outcomes",
        "scenario_bias",
        "stress_vector",
        "notes",
    ]
    lines = [
        f"memory_type: {memory_type}",
        preferred_lang_text(title_i18n, title_i18n.get("en", "")),
        f"title_ja: {title_i18n.get('ja', '')}",
        f"title_en: {title_i18n.get('en', '')}",
        f"title_th: {title_i18n.get('th', '')}",
    ]
    for key in fields:
        if key not in pattern:
            continue
        append_document_line(lines, key, pattern.get(key))
    return "\n".join(lines)


def extract_patterns_from_library(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("patterns", "items", "library", "entries"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "pattern_id" in data or "analog_id" in data:
            return [data]
    return []


def increment_stats(stats: BuildStats, memory_type: str) -> None:
    if memory_type == "prediction_snapshot":
        stats.prediction_snapshot += 1
    elif memory_type == "scenario_snapshot":
        stats.scenario_snapshot += 1
    elif memory_type == "signal_snapshot":
        stats.signal_snapshot += 1
    elif memory_type == "historical_pattern":
        stats.historical_pattern += 1
    elif memory_type == "historical_analog":
        stats.historical_analog += 1
    elif memory_type == "explanation":
        stats.explanation += 1
    else:
        stats.skipped += 1


def build_all_items(root: Path, include_history: bool) -> tuple[list[MemoryItem], BuildStats]:
    stats = BuildStats()
    items: list[MemoryItem] = []
    items.extend(build_decision_log_items(root, stats))
    if include_history:
        items.extend(build_prediction_history_items(root, stats))
    items.extend(build_historical_library_items(root, stats))
    items.extend(build_explanation_items(root, stats))
    return items, stats


def write_build_stamp(
    *,
    root: Path,
    qdrant_url: str,
    collection: str,
    embedding_model: str,
    indexed: int,
    stats: BuildStats,
) -> None:
    payload = {
        "generated_at": utc_now_iso(),
        "engine_version": "v1",
        "qdrant_url": qdrant_url,
        "collection": collection,
        "model": embedding_model,
        "indexed": indexed,
        "stats": stats.as_dict(),
        "source_scope": {
            "decision_log": "docs/core/decision_log.md",
            "prediction_history": "analysis/prediction/history",
            "historical": "analysis/historical",
            "explanation": "analysis/explanation",
        },
        "note": "Vector DB build stamp for freshness checking. reference_memory_latest.json is a recall artifact, not a build stamp.",
    }
    stamp_path = root / "analysis" / "prediction" / "vector_memory_build_latest.json"
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] repo root not found: {root}", file=sys.stderr)
        return 1

    try:
        client = QdrantClient(url=args.qdrant_url)
        client.set_model(args.embedding_model)
        ensure_collection(
            client=client,
            collection_name=args.collection,
            embedding_model=args.embedding_model,
            recreate=args.recreate,
        )
    except Exception as exc:
        print(f"[ERROR] qdrant setup failed: {exc}", file=sys.stderr)
        return 2

    items, stats = build_all_items(root=root, include_history=not args.no_history)
    if not items:
        print("[WARN] no items found to index")
        return 0

    try:
        add_items(
            client=client,
            collection_name=args.collection,
            items=items,
            batch_size=args.batch_size,
        )
    except Exception as exc:
        print(f"[ERROR] indexing failed: {exc}", file=sys.stderr)
        return 3

    write_build_stamp(
        root=root,
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        embedding_model=args.embedding_model,
        indexed=len(items),
        stats=stats,
    )

    print("[OK] vector memory build complete")
    print(f"  root       : {root}")
    print(f"  qdrant_url : {args.qdrant_url}")
    print(f"  collection : {args.collection}")
    print(f"  model      : {args.embedding_model}")
    print(f"  indexed    : {len(items)}")
    print(f"  stats      : {json.dumps(stats.as_dict(), ensure_ascii=False)}")
    print(f"  build_stamp: {VECTOR_MEMORY_BUILD_LATEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
