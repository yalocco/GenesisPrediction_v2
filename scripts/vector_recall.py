from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from qdrant_client import QdrantClient, models


DEFAULT_COLLECTION = "genesis_reference_memory"
DEFAULT_URL = "http://localhost:6333"
DEFAULT_MODEL = "BAAI/bge-small-en"
DEFAULT_LIMIT = 5
DEFAULT_TOP_K = 5
DEFAULT_COMPACT_SUMMARY_CHARS = 220

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

MEMORY_TYPE_ORDER = [
    "decision_log",
    "prediction_snapshot",
    "scenario_snapshot",
    "signal_snapshot",
    "historical_pattern",
    "historical_analog",
    "explanation",
]


def build_client(url: str) -> QdrantClient:
    return QdrantClient(url=url)


def _safe_get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    return getattr(obj, name, default)


def _extract_points(response: Any) -> List[Any]:
    """
    Normalize Qdrant responses across client versions.

    Observed shapes:
    - list[QueryResponse]
    - QueryResponse with .points
    - objects with .result or .result.points
    """
    if response is None:
        return []

    if isinstance(response, list):
        return response

    points = _safe_get(response, "points")
    if isinstance(points, list):
        return points

    result = _safe_get(response, "result")
    if isinstance(result, list):
        return result

    result_points = _safe_get(result, "points")
    if isinstance(result_points, list):
        return result_points

    return []


def _field(data: Dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in data:
            return data[name]
    return None


def _ensure_lang_map(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, str] = {}
    for lang in SUPPORTED_LANGUAGES:
        text = value.get(lang)
        if text is None:
            continue
        text_str = str(text).strip()
        if text_str:
            out[lang] = text_str
    return out


def _finalize_text_i18n(base_text: str, partial: Dict[str, str]) -> Dict[str, str]:
    en_text = str(partial.get("en") or base_text or "").strip()
    ja_text = str(partial.get("ja") or en_text).strip()
    th_text = str(partial.get("th") or en_text).strip()
    return {
        "en": en_text,
        "ja": ja_text,
        "th": th_text,
    }


def _pick_preferred_text(i18n_map: Dict[str, str], fallback: str = "") -> str:
    return (
        str(i18n_map.get(LANG_DEFAULT) or "").strip()
        or str(i18n_map.get("en") or "").strip()
        or fallback
    )


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return " ".join(text.replace("\r", "\n").replace("\n", " ").split()).strip()


def _clip_text(text: str, limit: int) -> str:
    text = _normalize_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _parse_csv_arg(values: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        for part in str(value).split(","):
            item = part.strip()
            if item and item not in out:
                out.append(item)
    return out


def _normalize_tags(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = str(item).strip().lower()
        if text and text not in out:
            out.append(text)
    return out


def _parse_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "static":
        return None

    for candidate in (text, text.replace("Z", "+00:00")):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue

    if len(text) >= 10:
        try:
            return datetime.fromisoformat(text[:10])
        except ValueError:
            return None

    return None


def _memory_type_rank(memory_type: Optional[str]) -> int:
    if not memory_type:
        return len(MEMORY_TYPE_ORDER) + 1
    try:
        return MEMORY_TYPE_ORDER.index(memory_type)
    except ValueError:
        return len(MEMORY_TYPE_ORDER)


def normalize_result_points(points: Iterable[Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []

    for p in points:
        payload = _safe_get(p, "payload", None)
        metadata = _safe_get(p, "metadata", None)
        document = _safe_get(p, "document", None)
        score = _safe_get(p, "score", None)

        data: Dict[str, Any] = {}
        if isinstance(payload, dict) and payload:
            data = payload
        elif isinstance(metadata, dict) and metadata:
            data = metadata

        title_raw = str(_field(data, "title") or "").strip()
        summary_raw = str(_field(data, "summary", "document") or "").strip()

        title_i18n = _finalize_text_i18n(
            title_raw,
            _ensure_lang_map(_field(data, "title_i18n")),
        )
        summary_i18n = _finalize_text_i18n(
            summary_raw,
            _ensure_lang_map(_field(data, "summary_i18n")),
        )

        normalized.append(
            {
                "score": float(score) if isinstance(score, (int, float)) else None,
                "memory_id": _field(data, "memory_id"),
                "memory_type": _field(data, "memory_type", "type"),
                "lang_default": str(_field(data, "lang_default") or LANG_DEFAULT).strip() or LANG_DEFAULT,
                "languages": _field(data, "languages") if isinstance(_field(data, "languages"), list) else list(SUPPORTED_LANGUAGES),
                "as_of": _field(data, "as_of", "date"),
                "title": _pick_preferred_text(title_i18n, title_raw),
                "title_i18n": title_i18n,
                "summary": _pick_preferred_text(summary_i18n, summary_raw),
                "summary_i18n": summary_i18n,
                "source_path": _field(data, "source_path", "source"),
                "source_kind": _field(data, "source_kind"),
                "tags": _normalize_tags(_field(data, "tags")),
                "overall_risk": _field(data, "overall_risk", "risk_level"),
                "dominant_scenario": _field(data, "dominant_scenario"),
                "confidence": _field(data, "confidence", "pattern_confidence", "analog_confidence"),
                "watchpoints": _field(data, "watchpoints"),
                "drivers": _field(data, "drivers"),
                "invalidation": _field(data, "invalidation", "invalidators", "invalidation_conditions"),
                "document": document,
                "metadata": metadata,
                "payload": payload,
            }
        )

    return normalized


def _build_query_filter(memory_types: Sequence[str] | None = None) -> Optional[models.Filter]:
    normalized_types = [t for t in memory_types or [] if str(t).strip()]
    if not normalized_types:
        return None

    if len(normalized_types) == 1:
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchValue(value=normalized_types[0]),
                )
            ]
        )

    return models.Filter(
        should=[
            models.FieldCondition(
                key="memory_type",
                match=models.MatchValue(value=value),
            )
            for value in normalized_types
        ]
    )


def _build_query_text(query: str = "", query_context: Optional[Dict[str, Any]] = None) -> str:
    parts: List[str] = []
    if query.strip():
        parts.append(query.strip())

    ctx = query_context or {}
    for key in (
        "source",
        "query",
        "trend_direction",
        "overall_risk",
        "dominant_scenario",
        "notes",
    ):
        value = ctx.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())

    for key in (
        "tags",
        "signal_tags",
        "drivers",
        "watchpoints",
        "supporting_signals",
    ):
        value = ctx.get(key)
        if isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if text:
                    parts.append(text)

    combined = " | ".join(dict.fromkeys(parts))
    return combined.strip()


def _tag_overlap_score(item_tags: Sequence[str], required_tags: Sequence[str]) -> float:
    if not required_tags:
        return 0.0
    item_set = {str(x).strip().lower() for x in item_tags if str(x).strip()}
    required_set = {str(x).strip().lower() for x in required_tags if str(x).strip()}
    if not required_set:
        return 0.0
    return len(item_set & required_set) / len(required_set)


def _date_in_range(as_of_value: Any, as_of_from: Optional[str], as_of_to: Optional[str]) -> bool:
    if not as_of_from and not as_of_to:
        return True

    dt = _parse_date(as_of_value)
    if dt is None:
        return False

    dt_from = _parse_date(as_of_from) if as_of_from else None
    dt_to = _parse_date(as_of_to) if as_of_to else None

    if dt_from is not None and dt < dt_from:
        return False
    if dt_to is not None and dt > dt_to:
        return False
    return True


def _recency_boost(as_of_value: Any, reference_date: Optional[str]) -> float:
    dt = _parse_date(as_of_value)
    ref = _parse_date(reference_date)
    if dt is None or ref is None:
        return 0.0

    delta_days = abs((ref.date() - dt.date()).days)
    if delta_days <= 7:
        return 0.12
    if delta_days <= 30:
        return 0.08
    if delta_days <= 90:
        return 0.04
    return 0.0


def _compute_reranked_score(
    item: Dict[str, Any],
    requested_memory_types: Sequence[str],
    requested_tags: Sequence[str],
    query_context: Optional[Dict[str, Any]],
    as_of_from: Optional[str],
    as_of_to: Optional[str],
) -> float:
    base_score = float(item.get("score") or 0.0)
    score = base_score

    if requested_memory_types and item.get("memory_type") in requested_memory_types:
        score += 0.08

    score += 0.18 * _tag_overlap_score(item.get("tags") or [], requested_tags)

    ctx = query_context or {}
    context_tags = _parse_csv_arg(ctx.get("tags") if isinstance(ctx.get("tags"), list) else [])
    signal_tags = _parse_csv_arg(ctx.get("signal_tags") if isinstance(ctx.get("signal_tags"), list) else [])
    if context_tags or signal_tags:
        score += 0.10 * _tag_overlap_score(item.get("tags") or [], context_tags + signal_tags)

    dominant_scenario = str(ctx.get("dominant_scenario") or "").strip().lower()
    if dominant_scenario and str(item.get("dominant_scenario") or "").strip().lower() == dominant_scenario:
        score += 0.08

    overall_risk = str(ctx.get("overall_risk") or "").strip().lower()
    if overall_risk and str(item.get("overall_risk") or "").strip().lower() == overall_risk:
        score += 0.06

    if _date_in_range(item.get("as_of"), as_of_from, as_of_to):
        score += 0.02
    else:
        score -= 0.15

    reference_date = str(ctx.get("as_of") or "").strip() or as_of_to or as_of_from
    score += _recency_boost(item.get("as_of"), reference_date)

    return score


def rerank_results(
    results: List[Dict[str, Any]],
    memory_types: Sequence[str] | None = None,
    tags: Sequence[str] | None = None,
    query_context: Optional[Dict[str, Any]] = None,
    as_of_from: Optional[str] = None,
    as_of_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    requested_memory_types = [str(x).strip() for x in memory_types or [] if str(x).strip()]
    requested_tags = [str(x).strip().lower() for x in tags or [] if str(x).strip()]

    reranked: List[Dict[str, Any]] = []
    for item in results:
        if requested_tags:
            overlap = _tag_overlap_score(item.get("tags") or [], requested_tags)
            if overlap <= 0:
                continue
        if not _date_in_range(item.get("as_of"), as_of_from, as_of_to):
            continue

        copy_item = dict(item)
        copy_item["rerank_score"] = _compute_reranked_score(
            item=item,
            requested_memory_types=requested_memory_types,
            requested_tags=requested_tags,
            query_context=query_context,
            as_of_from=as_of_from,
            as_of_to=as_of_to,
        )
        reranked.append(copy_item)

    reranked.sort(
        key=lambda x: (
            float(x.get("rerank_score") or 0.0),
            float(x.get("score") or 0.0),
            -_memory_type_rank(x.get("memory_type")),
        ),
        reverse=True,
    )
    return reranked


def search_similar(
    client: QdrantClient,
    collection: str,
    query: str = "",
    limit: int = DEFAULT_LIMIT,
    memory_types: Optional[Sequence[str]] = None,
    tags: Optional[Sequence[str]] = None,
    as_of_from: Optional[str] = None,
    as_of_to: Optional[str] = None,
    query_context: Optional[Dict[str, Any]] = None,
    rerank: bool = True,
) -> List[Dict[str, Any]]:
    """
    Semantic search using Qdrant's inference API.

    Prefer query_points(); fall back to deprecated query() if needed.
    Hybrid recall is applied by combining:
    - embedding similarity
    - memory_type filter
    - tag-aware rerank
    - date range filtering
    """
    search_text = _build_query_text(query=query, query_context=query_context)
    if not search_text:
        raise ValueError("search query is empty")

    normalized_memory_types = _parse_csv_arg(memory_types)
    query_filter = _build_query_filter(normalized_memory_types)

    response = None
    primary_error: Optional[Exception] = None

    try:
        response = client.query_points(
            collection_name=collection,
            query=models.Document(text=search_text, model=DEFAULT_MODEL),
            query_filter=query_filter,
            limit=max(limit * 3, limit),
            with_payload=True,
        )
    except Exception as exc:
        primary_error = exc

    if response is None:
        try:
            response = client.query(
                collection_name=collection,
                query_text=search_text,
                query_filter=query_filter,
                limit=max(limit * 3, limit),
            )
        except Exception as fallback_exc:
            if primary_error is not None:
                raise RuntimeError(
                    f"query_points failed: {primary_error}; fallback query failed: {fallback_exc}"
                ) from fallback_exc
            raise

    points = _extract_points(response)
    results = normalize_result_points(points)

    if rerank:
        results = rerank_results(
            results=results,
            memory_types=normalized_memory_types,
            tags=_parse_csv_arg(tags),
            query_context=query_context,
            as_of_from=as_of_from,
            as_of_to=as_of_to,
        )

    return results[:limit]


def compact_result(item: Dict[str, Any], summary_chars: int = DEFAULT_COMPACT_SUMMARY_CHARS) -> Dict[str, Any]:
    summary = item.get("summary") or item.get("document") or ""
    return {
        "score": item.get("score"),
        "rerank_score": item.get("rerank_score"),
        "memory_type": item.get("memory_type"),
        "as_of": item.get("as_of"),
        "title": item.get("title"),
        "summary": _clip_text(summary, summary_chars),
        "source_path": item.get("source_path"),
        "tags": item.get("tags") or [],
        "overall_risk": item.get("overall_risk"),
        "dominant_scenario": item.get("dominant_scenario"),
        "confidence": item.get("confidence"),
    }


def compact_results(results: List[Dict[str, Any]], summary_chars: int = DEFAULT_COMPACT_SUMMARY_CHARS) -> List[Dict[str, Any]]:
    return [compact_result(item, summary_chars=summary_chars) for item in results]


def _group_results(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped = {
        "decision_refs": [],
        "similar_cases": [],
        "historical_patterns": [],
        "historical_analogs": [],
        "explanations": [],
        "other": [],
    }

    for item in results:
        memory_type = str(item.get("memory_type") or "").strip()
        compact = compact_result(item)
        if memory_type == "decision_log":
            grouped["decision_refs"].append(compact)
        elif memory_type in {"prediction_snapshot", "scenario_snapshot", "signal_snapshot"}:
            grouped["similar_cases"].append(compact)
        elif memory_type == "historical_pattern":
            grouped["historical_patterns"].append(compact)
        elif memory_type == "historical_analog":
            grouped["historical_analogs"].append(compact)
        elif memory_type == "explanation":
            grouped["explanations"].append(compact)
        else:
            grouped["other"].append(compact)

    return grouped


def build_recall_summary(grouped: Dict[str, List[Dict[str, Any]]]) -> str:
    parts: List[str] = []
    if grouped["decision_refs"]:
        parts.append(f"decision_refs={len(grouped['decision_refs'])}")
    if grouped["similar_cases"]:
        parts.append(f"similar_cases={len(grouped['similar_cases'])}")
    if grouped["historical_patterns"]:
        parts.append(f"historical_patterns={len(grouped['historical_patterns'])}")
    if grouped["historical_analogs"]:
        parts.append(f"historical_analogs={len(grouped['historical_analogs'])}")
    if grouped["explanations"]:
        parts.append(f"explanations={len(grouped['explanations'])}")
    return ", ".join(parts) if parts else "no matching memory items"


def recall_for_context(
    client: QdrantClient,
    collection: str,
    query_context: Dict[str, Any],
    limit: int = DEFAULT_TOP_K,
) -> Dict[str, Any]:
    results = search_similar(
        client=client,
        collection=collection,
        query=str(query_context.get("query") or ""),
        limit=limit,
        memory_types=query_context.get("memory_types"),
        tags=query_context.get("tags"),
        as_of_from=query_context.get("as_of_from"),
        as_of_to=query_context.get("as_of_to"),
        query_context=query_context,
        rerank=True,
    )
    grouped = _group_results(results)
    return {
        "as_of": query_context.get("as_of"),
        "engine_version": "v1",
        "query_context": query_context,
        "decision_refs": grouped["decision_refs"],
        "similar_cases": grouped["similar_cases"],
        "historical_patterns": grouped["historical_patterns"],
        "historical_analogs": grouped["historical_analogs"],
        "explanations": grouped["explanations"],
        "recall_summary": build_recall_summary(grouped),
        "status": "ok" if results else "no_results",
    }


def recall_for_scenario_context(
    client: QdrantClient,
    collection: str,
    signal_tags: Optional[Sequence[str]] = None,
    trend_direction: str = "",
    drivers: Optional[Sequence[str]] = None,
    watchpoints: Optional[Sequence[str]] = None,
    overall_risk: str = "",
    dominant_scenario: str = "",
    as_of: str = "",
    limit: int = DEFAULT_TOP_K,
) -> Dict[str, Any]:
    signal_tags_list = _parse_csv_arg(signal_tags)
    drivers_list = _parse_csv_arg(drivers)
    watchpoints_list = _parse_csv_arg(watchpoints)

    context = {
        "source": "scenario_engine",
        "query": " ".join(
            part for part in [
                trend_direction.strip(),
                overall_risk.strip(),
                dominant_scenario.strip(),
                " ".join(signal_tags_list),
                " ".join(drivers_list),
                " ".join(watchpoints_list),
            ] if part
        ).strip(),
        "signal_tags": signal_tags_list,
        "drivers": drivers_list,
        "watchpoints": watchpoints_list,
        "trend_direction": trend_direction.strip(),
        "overall_risk": overall_risk.strip(),
        "dominant_scenario": dominant_scenario.strip(),
        "tags": signal_tags_list,
        "memory_types": [
            "decision_log",
            "prediction_snapshot",
            "scenario_snapshot",
            "signal_snapshot",
            "historical_pattern",
            "historical_analog",
        ],
        "as_of": as_of.strip(),
        "notes": "signal-driven + history-informed recall for scenario support",
    }
    return recall_for_context(
        client=client,
        collection=collection,
        query_context=context,
        limit=limit,
    )


def print_results(results: List[Dict[str, Any]], compact: bool = False) -> None:
    if not results:
        print("[INFO] no results")
        return

    print("\n=== Vector Recall Results ===\n")

    rows = compact_results(results) if compact else results

    for idx, item in enumerate(rows, start=1):
        score = item.get("score")
        score_text = f"{score:.4f}" if isinstance(score, (int, float)) else "n/a"
        rerank_score = item.get("rerank_score")
        rerank_text = f"{rerank_score:.4f}" if isinstance(rerank_score, (int, float)) else "n/a"

        summary = item.get("summary")
        if not summary:
            summary = item.get("document")

        print(f"[{idx}] score={score_text} rerank={rerank_text}")
        print(f"  memory_type: {item.get('memory_type')}")
        print(f"  as_of      : {item.get('as_of')}")
        print(f"  title      : {item.get('title')}")
        print(f"  summary    : {summary}")
        print(f"  source_path: {item.get('source_path')}")
        tags = item.get("tags")
        if tags is not None:
            print(f"  tags       : {tags}")
        if item.get("dominant_scenario") is not None:
            print(f"  scenario   : {item.get('dominant_scenario')}")
        if item.get("overall_risk") is not None:
            print(f"  risk       : {item.get('overall_risk')}")
        if item.get("confidence") is not None:
            print(f"  confidence : {item.get('confidence')}")
        print("")


def _load_json_file(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic recall from GenesisPrediction vector memory.")
    parser.add_argument("--query", default="", help="Search query text")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum number of results")
    parser.add_argument("--url", default=DEFAULT_URL, help="Qdrant URL")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
    parser.add_argument(
        "--memory-type",
        action="append",
        default=[],
        help="Optional filter. Repeat or use comma-separated values.",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Optional tag filter for rerank. Repeat or use comma-separated values.",
    )
    parser.add_argument("--as-of-from", default=None, help="Optional inclusive date filter (YYYY-MM-DD)")
    parser.add_argument("--as-of-to", default=None, help="Optional inclusive date filter (YYYY-MM-DD)")
    parser.add_argument(
        "--query-context-json",
        default=None,
        help="Optional JSON string with query context fields.",
    )
    parser.add_argument(
        "--query-context-file",
        default=None,
        help="Optional JSON file path with query context fields.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact results.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print normalized results as JSON.",
    )
    parser.add_argument(
        "--scenario-context",
        action="store_true",
        help="Emit reference_memory-style JSON for scenario integration.",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Disable lightweight hybrid rerank.",
    )

    args = parser.parse_args()

    query_context: Dict[str, Any] = {}
    if args.query_context_json:
        query_context.update(json.loads(args.query_context_json))
    if args.query_context_file:
        query_context.update(_load_json_file(args.query_context_file))

    client = build_client(args.url)

    if args.scenario_context:
        if args.query:
            query_context["query"] = args.query
        if args.memory_type:
            query_context["memory_types"] = _parse_csv_arg(args.memory_type)
        if args.tag:
            query_context["tags"] = _parse_csv_arg(args.tag)
        if args.as_of_from:
            query_context["as_of_from"] = args.as_of_from
        if args.as_of_to:
            query_context["as_of_to"] = args.as_of_to

        artifact = recall_for_context(
            client=client,
            collection=args.collection,
            query_context=query_context,
            limit=args.limit,
        )
        print(json.dumps(artifact, ensure_ascii=False, indent=2))
        return

    results = search_similar(
        client=client,
        collection=args.collection,
        query=args.query,
        limit=args.limit,
        memory_types=_parse_csv_arg(args.memory_type),
        tags=_parse_csv_arg(args.tag),
        as_of_from=args.as_of_from,
        as_of_to=args.as_of_to,
        query_context=query_context,
        rerank=not args.no_rerank,
    )

    if args.json:
        output = compact_results(results) if args.compact else results
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print_results(results, compact=args.compact)


if __name__ == "__main__":
    main()
