from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.processing.embedder import VoyageEmbedder
from app.rag.agent import RAGAgent
from app.rag.recommender import PersonalizedRecommender
from app.rag.retriever import VectorRetriever
from app.storage.mongo import get_database


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


_embedder: VoyageEmbedder | None = None


def get_embedder() -> VoyageEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = VoyageEmbedder()
    return _embedder


def get_retriever(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    embedder: Annotated[VoyageEmbedder, Depends(get_embedder)],
) -> VectorRetriever:
    return VectorRetriever(db, embedder)


def get_rag_agent(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    retriever: Annotated[VectorRetriever, Depends(get_retriever)],
) -> RAGAgent:
    return RAGAgent(retriever, db)


def get_recommender(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    embedder: Annotated[VoyageEmbedder, Depends(get_embedder)],
    retriever: Annotated[VectorRetriever, Depends(get_retriever)],
) -> PersonalizedRecommender:
    return PersonalizedRecommender(db, embedder, retriever)
