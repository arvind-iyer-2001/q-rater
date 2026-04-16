from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING

from app.config import get_settings
from app.storage.models import ContentDocument, UserProfile

settings = get_settings()

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_client()[settings.mongodb_db_name]


async def close_client() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


# ---------------------------------------------------------------------------
# Index setup
# ---------------------------------------------------------------------------

async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    content_col = db[settings.mongodb_collection_content]
    await content_col.create_indexes([
        IndexModel([("content_id", ASCENDING)], unique=True),
        IndexModel([("job_id", ASCENDING)]),
        IndexModel([("url", ASCENDING)], unique=True),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("source", ASCENDING)]),
    ])

    users_col = db[settings.mongodb_collection_users]
    await users_col.create_indexes([
        IndexModel([("user_id", ASCENDING)], unique=True),
    ])


# ---------------------------------------------------------------------------
# Content CRUD
# ---------------------------------------------------------------------------

async def upsert_content(db: AsyncIOMotorDatabase, doc: ContentDocument) -> str:
    doc.updated_at = datetime.now(timezone.utc)
    col = db[settings.mongodb_collection_content]
    await col.replace_one(
        {"content_id": doc.content_id},
        doc.model_dump(),
        upsert=True,
    )
    return doc.content_id


async def get_content_by_id(
    db: AsyncIOMotorDatabase, content_id: str
) -> Optional[dict]:
    col = db[settings.mongodb_collection_content]
    return await col.find_one({"content_id": content_id}, {"_id": 0})


async def get_content_by_url(
    db: AsyncIOMotorDatabase, url: str
) -> Optional[dict]:
    col = db[settings.mongodb_collection_content]
    return await col.find_one({"url": url}, {"_id": 0})


async def get_content_by_job_id(
    db: AsyncIOMotorDatabase, job_id: str
) -> Optional[dict]:
    col = db[settings.mongodb_collection_content]
    return await col.find_one({"job_id": job_id}, {"_id": 0})


async def list_content(
    db: AsyncIOMotorDatabase,
    source: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    col = db[settings.mongodb_collection_content]
    query: dict[str, Any] = {"status": "complete"}
    if source:
        query["source"] = source
    cursor = col.find(query, {"_id": 0, "embeddings": 0, "raw": 0}).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def update_job_status(
    db: AsyncIOMotorDatabase,
    job_id: str,
    status: str,
    progress: int = 0,
    error: Optional[str] = None,
) -> None:
    col = db[settings.mongodb_collection_content]
    update: dict[str, Any] = {
        "$set": {
            "status": status,
            "progress": progress,
            "updated_at": datetime.now(timezone.utc),
        }
    }
    if error is not None:
        update["$set"]["error"] = error
    await col.update_one({"job_id": job_id}, update)


# ---------------------------------------------------------------------------
# Vector search
# ---------------------------------------------------------------------------

async def vector_search(
    db: AsyncIOMotorDatabase,
    query_embedding: list[float],
    source_filter: Optional[str] = None,
    content_type_filter: Optional[str] = None,
    limit: int = 10,
    num_candidates: int = 150,
) -> list[dict]:
    col = db[settings.mongodb_collection_content]

    vector_search_stage: dict[str, Any] = {
        "$vectorSearch": {
            "index": settings.mongodb_vector_index_name,
            "path": "embeddings.combined",
            "queryVector": query_embedding,
            "numCandidates": num_candidates,
            "limit": limit,
        }
    }

    # Add pre-filters if provided (requires filter-type fields in the Atlas index)
    filter_conditions: dict[str, Any] = {}
    if source_filter:
        filter_conditions["source"] = {"$eq": source_filter}
    if content_type_filter:
        filter_conditions["summary.content_type"] = {"$eq": content_type_filter}
    if filter_conditions:
        vector_search_stage["$vectorSearch"]["filter"] = filter_conditions

    pipeline = [
        vector_search_stage,
        {
            "$project": {
                "_id": 0,
                "score": {"$meta": "vectorSearchScore"},
                "content_id": 1,
                "url": 1,
                "source": 1,
                "metadata": 1,
                "summary": 1,
            }
        },
    ]

    cursor = col.aggregate(pipeline)
    return await cursor.to_list(length=limit)


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

async def upsert_user(db: AsyncIOMotorDatabase, user: UserProfile) -> str:
    user.updated_at = datetime.now(timezone.utc)
    col = db[settings.mongodb_collection_users]
    await col.replace_one(
        {"user_id": user.user_id},
        user.model_dump(),
        upsert=True,
    )
    return user.user_id


async def get_user(
    db: AsyncIOMotorDatabase, user_id: str
) -> Optional[dict]:
    col = db[settings.mongodb_collection_users]
    return await col.find_one({"user_id": user_id}, {"_id": 0})


async def mark_content_viewed(
    db: AsyncIOMotorDatabase, user_id: str, content_id: str
) -> None:
    col = db[settings.mongodb_collection_users]
    await col.update_one(
        {"user_id": user_id},
        {"$addToSet": {"viewed_content_ids": content_id}},
    )
