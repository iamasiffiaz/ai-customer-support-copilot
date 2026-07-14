"""Qdrant vector store with in-memory fallback."""

from __future__ import annotations

import math
from typing import Any, Optional

from config import get_settings
from services.embedding_service import EMBED_DIM

settings = get_settings()

_memory_store: dict[str, list[dict[str, Any]]] = {}
_qdrant_client = None
_qdrant_available: Optional[bool] = None


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _try_qdrant():
    global _qdrant_client, _qdrant_available
    if _qdrant_available is False:
        return None
    if _qdrant_client is not None:
        return _qdrant_client
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qmodels

        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None, timeout=5)
        # ping
        client.get_collections()
        collection = settings.qdrant_collection
        existing = [c.name for c in client.get_collections().collections]
        if collection not in existing:
            client.create_collection(
                collection_name=collection,
                vectors_config=qmodels.VectorParams(size=EMBED_DIM, distance=qmodels.Distance.COSINE),
            )
        _qdrant_client = client
        _qdrant_available = True
        return client
    except Exception:
        _qdrant_available = False
        _qdrant_client = None
        return None


def upsert_embeddings(points: list[dict[str, Any]]) -> bool:
    """points: [{id, vector, payload}]"""
    client = _try_qdrant()
    if client:
        from qdrant_client.http import models as qmodels

        client.upsert(
            collection_name=settings.qdrant_collection,
            points=[
                qmodels.PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload") or {})
                for p in points
            ],
        )
        return True

    coll = settings.qdrant_collection
    store = _memory_store.setdefault(coll, [])
    by_id = {p["id"]: i for i, p in enumerate(store)}
    for p in points:
        item = {"id": p["id"], "vector": p["vector"], "payload": p.get("payload") or {}}
        if p["id"] in by_id:
            store[by_id[p["id"]]] = item
        else:
            store.append(item)
    return True


def search_vectors(query_vector: list[float], limit: int = 5, document_id: Optional[int] = None) -> list[dict[str, Any]]:
    client = _try_qdrant()
    if client:
        from qdrant_client.http import models as qmodels

        query_filter = None
        if document_id is not None:
            query_filter = qmodels.Filter(
                must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
            )
        results = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        return [
            {
                "id": r.id,
                "score": float(r.score),
                "payload": r.payload or {},
            }
            for r in results
        ]

    store = _memory_store.get(settings.qdrant_collection, [])
    scored = []
    for item in store:
        payload = item.get("payload") or {}
        if document_id is not None and payload.get("document_id") != document_id:
            continue
        scored.append(
            {
                "id": item["id"],
                "score": _cosine(query_vector, item["vector"]),
                "payload": payload,
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def delete_by_document(document_id: int) -> None:
    client = _try_qdrant()
    if client:
        from qdrant_client.http import models as qmodels

        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
                )
            ),
        )
        return

    store = _memory_store.get(settings.qdrant_collection, [])
    _memory_store[settings.qdrant_collection] = [
        p for p in store if (p.get("payload") or {}).get("document_id") != document_id
    ]
