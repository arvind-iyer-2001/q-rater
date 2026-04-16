from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db, get_rag_agent, get_recommender
from app.rag.agent import RAGAgent
from app.rag.recommender import PersonalizedRecommender
from app.storage.models import (
    RecommendationResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    UpdateInterestsRequest,
    UserProfile,
)
from app.storage.mongo import get_user, upsert_user

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    agent: Annotated[RAGAgent, Depends(get_rag_agent)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> SearchResponse:
    user_profile: Optional[UserProfile] = None
    if payload.user_id:
        user_doc = await get_user(db, payload.user_id)
        if user_doc:
            user_profile = UserProfile(**user_doc)

    result = await agent.query(
        user_query=payload.query,
        user_profile=user_profile,
    )

    sources = [
        SearchResult(
            content_id=s.get("content_id", ""),
            url=s.get("url", ""),
            source=s.get("source", ""),
            score=float(s.get("score", 0)),
            metadata=s.get("metadata", {}),
            summary=s.get("summary", {}),
        )
        for s in result.sources[:payload.limit]
    ]

    return SearchResponse(answer=result.answer, sources=sources)


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: str = Query(..., description="User ID for personalized recommendations"),
    limit: int = Query(default=10, ge=1, le=50),
    exclude_seen: bool = Query(default=True),
    recommender: PersonalizedRecommender = Depends(get_recommender),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RecommendationResponse:
    user_doc = await get_user(db, user_id)
    if user_doc:
        user = UserProfile(**user_doc)
    else:
        # Create a blank profile on first access
        user = UserProfile(user_id=user_id)
        await upsert_user(db, user)

    items_raw = await recommender.get_recommendations(
        user=user, exclude_seen=exclude_seen, limit=limit
    )
    items = [
        SearchResult(
            content_id=s.get("content_id", ""),
            url=s.get("url", ""),
            source=s.get("source", ""),
            score=float(s.get("score", 0)),
            metadata=s.get("metadata", {}),
            summary=s.get("summary", {}),
        )
        for s in items_raw
    ]
    return RecommendationResponse(items=items)


@router.post("/users/{user_id}/interests", response_model=dict)
async def update_interests(
    user_id: str,
    payload: UpdateInterestsRequest,
    recommender: Annotated[PersonalizedRecommender, Depends(get_recommender)],
) -> dict:
    user = await recommender.update_user_interests(user_id, payload.interests)
    return {"user_id": user.user_id, "interests": user.interests}
