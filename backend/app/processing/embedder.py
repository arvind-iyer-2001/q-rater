from __future__ import annotations

import asyncio
from typing import Optional

from app.config import get_settings

settings = get_settings()


class VoyageEmbedder:
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            import voyageai
            self._client = voyageai.Client(api_key=settings.voyage_api_key)
        return self._client

    async def embed_texts(
        self, texts: list[str], input_type: str = "document"
    ) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._get_client().embed(
                texts, model=settings.embedding_model, input_type=input_type
            ),
        )
        return result.embeddings

    async def embed_pair(
        self, combined_text: str, summary_text: str
    ) -> dict[str, list[float]]:
        embeddings = await self.embed_texts([combined_text, summary_text], input_type="document")
        return {
            "combined": embeddings[0] if len(embeddings) > 0 else [],
            "summary_only": embeddings[1] if len(embeddings) > 1 else [],
        }

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await self.embed_texts([query], input_type="query")
        return embeddings[0] if embeddings else []
