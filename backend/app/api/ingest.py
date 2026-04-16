from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.storage.models import (
    ContentDocument,
    IngestRequest,
    IngestResponse,
    JobStatusResponse,
)
from app.storage.mongo import (
    get_content_by_job_id,
    get_content_by_url,
    upsert_content,
)
from app.utils.url_parser import detect_platform

router = APIRouter(prefix="/ingest", tags=["ingest"])


async def _enqueue_ingest(job_id: str, content_id: str, url: str, db: AsyncIOMotorDatabase) -> None:
    """Background task wrapper — tries ARQ first, falls back to in-process."""
    try:
        import arq
        from app.config import get_settings
        settings = get_settings()
        redis = await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
        await redis.enqueue_job("run_ingest_job", job_id, content_id, url)
        await redis.close()
    except Exception:
        # Fallback: run directly in background task (no Redis required for dev)
        from app.ingestion.dispatcher import IngestDispatcher
        from app.processing.pipeline import ProcessingPipeline
        from app.storage.mongo import update_job_status
        import traceback

        try:
            dispatcher = IngestDispatcher()
            raw = await dispatcher.ingest(url, content_id)
            pipeline = ProcessingPipeline()
            doc = await pipeline.process(raw, job_id, db)
            await upsert_content(db, doc)
        except Exception as exc:
            await update_job_status(db, job_id, "failed", error=str(exc))


@router.post("", response_model=IngestResponse, status_code=202)
async def ingest_url(
    payload: IngestRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> IngestResponse:
    url = payload.url.strip()

    platform = detect_platform(url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only YouTube and Instagram URLs are supported.")

    # Dedup: return existing job if URL already ingested
    existing = await get_content_by_url(db, url)
    if existing:
        return IngestResponse(
            job_id=existing["job_id"],
            content_id=existing["content_id"],
            status=existing["status"],
        )

    job_id = str(uuid4())
    content_id = str(uuid4())

    # Create a placeholder document so status polling works immediately
    placeholder = ContentDocument(
        content_id=content_id,
        source=platform,
        url=url,
        job_id=job_id,
        status="pending",
        progress=0,
    )
    await upsert_content(db, placeholder)

    background_tasks.add_task(_enqueue_ingest, job_id, content_id, url, db)

    return IngestResponse(job_id=job_id, content_id=content_id, status="pending")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> JobStatusResponse:
    doc = await get_content_by_job_id(db, job_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=doc["job_id"],
        content_id=doc["content_id"],
        status=doc["status"],
        progress=doc.get("progress", 0),
        error=doc.get("error"),
    )
