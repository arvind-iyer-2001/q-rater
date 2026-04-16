from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.processing.embedder import VoyageEmbedder
from app.rag.retriever import VectorRetriever
from app.storage.models import UserProfile
from app.storage.mongo import upsert_user, get_user


class PersonalizedRecommender:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        embedder: VoyageEmbedder,
        retriever: VectorRetriever,
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.retriever = retriever

    async def get_recommendations(
        self,
        user: UserProfile,
        exclude_seen: bool = True,
        limit: int = 10,
    ) -> list[dict]:
        if not user.interests:
            # No interests: return recent content ranked by quality
            return await self._get_popular(limit)

        # Build interest embedding
        interest_text = ", ".join(user.interests)
        embedding = await self.embedder.embed_query(interest_text)

        # Fetch more than needed if filtering seen content
        fetch_limit = limit + len(user.viewed_content_ids) if exclude_seen else limit
        fetch_limit = min(fetch_limit, 100)

        results = await self.retriever.search_by_embedding(
            embedding=embedding,
            limit=fetch_limit,
        )

        if exclude_seen:
            seen = set(user.viewed_content_ids)
            results = [r for r in results if r.get("content_id") not in seen]

        return results[:limit]

    async def _get_popular(self, limit: int) -> list[dict]:
        from app.storage.mongo import list_content
        items = await list_content(self.db, limit=limit)
        return [
            {
                "content_id": item.get("content_id", ""),
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "score": item.get("summary", {}).get("quality_score", 0.0),
                "metadata": item.get("metadata", {}),
                "summary": item.get("summary", {}),
            }
            for item in items
        ]

    async def update_user_interests(
        self,
        user_id: str,
        interests: list[str],
    ) -> UserProfile:
        existing = await get_user(self.db, user_id)
        if existing:
            user = UserProfile(**existing)
        else:
            user = UserProfile(user_id=user_id)

        user.interests = interests

        # Pre-compute interest embedding for fast recommendation lookups
        if interests:
            interest_text = ", ".join(interests)
            user.interest_embedding = await self.embedder.embed_query(interest_text)

        await upsert_user(self.db, user)
        return user
