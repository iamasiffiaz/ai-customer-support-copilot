"""RAG orchestration: retrieve KB chunks and prepare citation payloads."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from config import get_settings
from models import KnowledgeBaseChunk, KnowledgeBaseDocument
from services.embedding_service import embed_query
from services.vector_service import search_vectors

settings = get_settings()


def search_knowledge_base(
    db: Session,
    query: str,
    limit: Optional[int] = None,
    min_score: Optional[float] = None,
) -> list[dict[str, Any]]:
    top_k = limit or settings.rag_top_k
    threshold = settings.rag_min_score if min_score is None else min_score
    vector = embed_query(query)
    hits = search_vectors(vector, limit=top_k)
    results: list[dict[str, Any]] = []

    for hit in hits:
        payload = hit.get("payload") or {}
        chunk_id = payload.get("chunk_id")
        content = payload.get("content")
        document_id = payload.get("document_id")
        document_title = payload.get("document_title")
        score = float(hit.get("score") or 0)

        if chunk_id and (not content or not document_title):
            chunk = db.query(KnowledgeBaseChunk).filter(KnowledgeBaseChunk.id == chunk_id).first()
            if chunk:
                content = content or chunk.content
                document_id = document_id or chunk.document_id
                if not document_title and chunk.document:
                    document_title = chunk.document.title

        if not content or score < threshold:
            continue

        results.append(
            {
                "chunk_id": chunk_id or hit.get("id"),
                "document_id": document_id,
                "document_title": document_title or "Knowledge Base",
                "content": content,
                "score": score,
            }
        )

    # Keyword fallback when vector hits are weak/empty
    if len(results) < max(2, top_k // 2):
        stop = {"how", "do", "we", "the", "a", "an", "to", "for", "of", "is", "what", "if", "i", "in", "on"}
        terms = [t for t in (query or "").lower().replace("?", "").split() if len(t) > 2 and t not in stop]
        if not terms:
            terms = [(query or "policy").split()[0]]
        existing_ids = {r["chunk_id"] for r in results}
        for term in terms:
            chunks = (
                db.query(KnowledgeBaseChunk)
                .filter(KnowledgeBaseChunk.content.ilike(f"%{term}%"))
                .limit(top_k)
                .all()
            )
            for chunk in chunks:
                if chunk.id in existing_ids:
                    continue
                doc = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.id == chunk.document_id).first()
                results.append(
                    {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_title": doc.title if doc else "Knowledge Base",
                        "content": chunk.content,
                        "score": 0.55,
                    }
                )
                existing_ids.add(chunk.id)
                if len(results) >= top_k:
                    break
            if len(results) >= top_k:
                break

    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return results[:top_k]


def build_context_block(chunks: list[dict[str, Any]]) -> str:
    return "\n\n".join(f"[{c.get('document_title')}] {c.get('content')}" for c in chunks)
