import argparse
import json
from typing import Any, Dict, Iterable, List, Optional

from qdrant_client import QdrantClient, models


DEFAULT_COLLECTION = "genesis_reference_memory"
DEFAULT_URL = "http://localhost:6333"
DEFAULT_MODEL = "BAAI/bge-small-en"

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]


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


def normalize_result_points(points: Iterable[Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []

    for p in points:
        payload = _safe_get(p, "payload", None)
        metadata = _safe_get(p, "metadata", None)
        document = _safe_get(p, "document", None)
        score = _safe_get(p, "score", None)

        # FastEmbed query() often returns metadata/document instead of payload
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
                "score": score,
                "memory_type": _field(data, "memory_type", "type"),
                "lang_default": str(_field(data, "lang_default") or LANG_DEFAULT).strip() or LANG_DEFAULT,
                "languages": _field(data, "languages") if isinstance(_field(data, "languages"), list) else list(SUPPORTED_LANGUAGES),
                "as_of": _field(data, "as_of", "date"),
                "title": _pick_preferred_text(title_i18n, title_raw),
                "title_i18n": title_i18n,
                "summary": _pick_preferred_text(summary_i18n, summary_raw),
                "summary_i18n": summary_i18n,
                "source_path": _field(data, "source_path", "source"),
                "tags": _field(data, "tags"),
                "document": document,
                "metadata": metadata,
                "payload": payload,
            }
        )

    return normalized


def search_similar(
    client: QdrantClient,
    collection: str,
    query: str,
    limit: int = 5,
    memory_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic search using Qdrant's inference API.

    Prefer query_points(); fall back to deprecated query() if needed.
    """
    query_filter = None
    if memory_type:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchValue(value=memory_type),
                )
            ]
        )

    response = None
    primary_error: Optional[Exception] = None

    try:
        response = client.query_points(
            collection_name=collection,
            query=models.Document(text=query, model=DEFAULT_MODEL),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
    except Exception as exc:
        primary_error = exc

    if response is None:
        try:
            response = client.query(
                collection_name=collection,
                query_text=query,
                query_filter=query_filter,
                limit=limit,
            )
        except Exception as fallback_exc:
            if primary_error is not None:
                raise RuntimeError(
                    f"query_points failed: {primary_error}; fallback query failed: {fallback_exc}"
                ) from fallback_exc
            raise

    points = _extract_points(response)
    return normalize_result_points(points)


def print_results(results: List[Dict[str, Any]]) -> None:
    if not results:
        print("[INFO] no results")
        return

    print("\n=== Vector Recall Results ===\n")

    for idx, item in enumerate(results, start=1):
        score = item.get("score")
        score_text = f"{score:.4f}" if isinstance(score, (int, float)) else "n/a"

        summary = item.get("summary")
        if not summary:
            summary = item.get("document")

        print(f"[{idx}] score={score_text}")
        print(f"  memory_type: {item.get('memory_type')}")
        print(f"  as_of      : {item.get('as_of')}")
        print(f"  title      : {item.get('title')}")
        print(f"  summary    : {summary}")
        print(f"  source_path: {item.get('source_path')}")
        tags = item.get("tags")
        if tags is not None:
            print(f"  tags       : {tags}")
        print("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic recall from GenesisPrediction vector memory.")
    parser.add_argument("--query", required=True, help="Search query text")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    parser.add_argument("--url", default=DEFAULT_URL, help="Qdrant URL")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
    parser.add_argument(
        "--memory-type",
        default=None,
        help="Optional filter: decision_log | prediction_snapshot | scenario_snapshot | signal_snapshot | historical_pattern | historical_analog | explanation",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print normalized results as JSON",
    )

    args = parser.parse_args()

    client = build_client(args.url)
    results = search_similar(
        client=client,
        collection=args.collection,
        query=args.query,
        limit=args.limit,
        memory_type=args.memory_type,
    )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print_results(results)


if __name__ == "__main__":
    main()