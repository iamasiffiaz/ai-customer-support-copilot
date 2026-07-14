"""Embedding generation with API or deterministic mock vectors."""

from __future__ import annotations

import hashlib
import logging
import math

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
EMBED_DIM = settings.embedding_dimensions


def _mock_embed(text: str, dim: int = EMBED_DIM) -> list[float]:
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    values: list[float] = []
    seed = digest
    while len(values) < dim:
        for b in seed:
            values.append(((b / 255.0) * 2) - 1)
            if len(values) >= dim:
                break
        seed = hashlib.sha256(seed).digest()
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.openai_api_key:
        return [_mock_embed(t) for t in texts]
    try:
        payload: dict = {"model": settings.embedding_model, "input": texts}
        # Pin dimensions when the provider supports it (OpenAI text-embedding-3-*)
        if settings.embedding_dimensions:
            payload["dimensions"] = settings.embedding_dimensions
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{settings.openai_base_url.rstrip('/')}/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = sorted(resp.json()["data"], key=lambda x: x["index"])
            vectors = [row["embedding"] for row in data]
            # Guard against unexpected dimensions
            if vectors and len(vectors[0]) != EMBED_DIM:
                logger.warning(
                    "Embedding dim mismatch (%s != %s); using mock vectors",
                    len(vectors[0]),
                    EMBED_DIM,
                )
                return [_mock_embed(t) for t in texts]
            return vectors
    except Exception as exc:
        logger.warning("Embedding API failed; using mock vectors: %s", exc)
        return [_mock_embed(t) for t in texts]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
