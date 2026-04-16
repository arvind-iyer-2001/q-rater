from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.processing.embedder import VoyageEmbedder
from app.storage.mongo import vector_search


class VectorRetriever:
    def __init__(self, db: AsyncIOMotorDatabase, embedder: VoyageEmbedder) -> None:
        self.db = db
        self.embedder = embedder

    async def search(
        self,
        query: str,
        source_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        embedding = await self.embedder.embed_query(query)
        if not embedding:
            return []
        return await vector_search(
            self.db,
            query_embedding=embedding,
            source_filter=source_filter if source_filter != "any" else None,
            content_type_filter=content_type_filter,
            limit=limit,
        )

    async def search_by_embedding(
        self,
        embedding: list[float],
        source_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        return await vector_search(
            self.db,
            query_embedding=embedding,
            source_filter=source_filter,
            content_type_filter=content_type_filter,
            limit=limit,
        )
