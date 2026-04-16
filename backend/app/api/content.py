from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.storage.mongo import get_content_by_id, list_content

router = APIRouter(prefix="/content", tags=["content"])


@router.get("", response_model=list[dict])
async def list_all_content(
    source: Optional[str] = Query(default=None, pattern="^(youtube|instagram)$"),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[dict]:
    return await list_content(db, source=source, limit=limit, skip=skip)


@router.get("/{content_id}", response_model=dict)
async def get_content(
    content_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> dict:
    doc = await get_content_by_id(db, content_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    # Exclude large embedding vectors from the API response
    doc.pop("embeddings", None)
    return doc
