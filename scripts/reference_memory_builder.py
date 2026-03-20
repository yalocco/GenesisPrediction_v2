import json
import os
from datetime import datetime, UTC
from typing import Any, Dict, List

from qdrant_client import QdrantClient, models

# =========================
# CONFIG
# =========================
QDRANT_URL = "http://localhost:6333"
COLLECTION = "genesis_reference_memory"

OUTPUT_PATH = "analysis/prediction/reference_memory_latest.json"

TOP_K = 3


# =========================
# UTIL
# =========================
def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_query_context() -> Dict[str, Any]:
    """
    Build recall query from:
    - signal_latest
    - trend_latest
    """

    signal = load_json("analysis/signal/signal_latest.json")
    trend = load_json("analysis/trend/trend_latest.json")

    tags: List[str] = []
    notes: List[str] = []

    # Signal tags
    if isinstance(signal.get("tags"), list):
        tags.extend(signal.get("tags", []))

    # Trend summary
    if trend.get("trend_summary"):
        notes.append(trend.get("trend_summary"))

    # fallback
    if not tags and not notes:
        notes.append("macro stress environment")

    query_text = " ".join(tags + notes)

    return {
        "query_text": query_text,
        "tags": tags,
        "notes": notes,
    }


def build_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


# =========================
# VECTOR SEARCH（安定版）
# =========================
def query_memory(
    client: QdrantClient,
    query_text: str,
    memory_type: str,
    limit: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Stable version using query() for FastEmbed collections
    """
    try:
        response = client.query(
            collection_name=COLLECTION,
            query_text=query_text,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="memory_type",
                        match=models.MatchValue(value=memory_type),
                    )
                ]
            ),
            limit=limit,
        )

        results = []
        for p in response:
            meta = getattr(p, "metadata", None) or getattr(p, "payload", None) or {}

            results.append(
                {
                    "score": getattr(p, "score", None),
                    "memory_type": meta.get("memory_type"),
                    "title": meta.get("title"),
                    "summary": meta.get("summary"),
                    "source_path": meta.get("source_path"),
                    "as_of": meta.get("as_of"),
                    "tags": meta.get("tags"),
                }
            )

        return results

    except Exception as e:
        print(f"[WARN] recall failed for {memory_type}: {e}")
        return []


# =========================
# MAIN BUILDER
# =========================
def build_reference_memory() -> Dict[str, Any]:
    client = build_client()

    context = build_query_context()
    query_text = context["query_text"]

    # memory buckets
    decision_refs = query_memory(client, query_text, "decision_log")
    historical_patterns = query_memory(client, query_text, "historical_pattern")
    historical_analogs = query_memory(client, query_text, "historical_analog")
    similar_cases = query_memory(client, query_text, "prediction_snapshot")

    # summary generation
    summary_parts = []

    if historical_patterns:
        summary_parts.append(
            f"dominant_pattern={historical_patterns[0].get('title')}"
        )

    if historical_analogs:
        summary_parts.append(
            f"dominant_analog={historical_analogs[0].get('title')}"
        )

    recall_summary = " | ".join(summary_parts) if summary_parts else "no strong recall"

    # status
    if decision_refs or historical_patterns or historical_analogs or similar_cases:
        status = "ok"
    else:
        status = "empty"

    return {
        "as_of": datetime.now(UTC).strftime("%Y-%m-%d"),
        "engine_version": "v1",
        "query_context": {
            "source": "scenario_engine",
            "tags": context["tags"],
            "notes": context["notes"],
            "query_text": query_text,
        },
        "decision_refs": decision_refs,
        "similar_cases": similar_cases,
        "historical_patterns": historical_patterns,
        "historical_analogs": historical_analogs,
        "recall_summary": recall_summary,
        "status": status,
        "generated_at": datetime.now(UTC).isoformat(),
    }


# =========================
# ENTRY POINT
# =========================
def main():
    print("[INFO] Building reference memory...")

    result = build_reference_memory()

    save_json(OUTPUT_PATH, result)

    print("[OK] reference_memory_latest.json updated")
    print(f"  status: {result['status']}")
    print(f"  summary: {result['recall_summary']}")


if __name__ == "__main__":
    main()