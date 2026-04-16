"""ARQ worker — runs as a separate process alongside the FastAPI app.

Start with:
    arq app.tasks.worker.WorkerSettings
"""
from __future__ import annotations

import traceback
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.ingestion.dispatcher import IngestDispatcher
from app.processing.pipeline import ProcessingPipeline
from app.storage.mongo import upsert_content, update_job_status

settings = get_settings()


async def run_ingest_job(ctx: dict[str, Any], job_id: str, content_id: str, url: str) -> dict:
    """ARQ task: ingest and process a URL, persist the resulting ContentDocument."""
    db = ctx["db"]

    try:
        await update_job_status(db, job_id, "processing", progress=5)

        dispatcher = IngestDispatcher()
        raw_media = await dispatcher.ingest(url, content_id)

        pipeline = ProcessingPipeline()
        doc = await pipeline.process(raw_media, job_id, db)

        await upsert_content(db, doc)
        await update_job_status(db, job_id, "complete", progress=100)

        return {"status": "complete", "content_id": content_id}

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        tb = traceback.format_exc()
        await update_job_status(db, job_id, "failed", error=error_msg)
        return {"status": "failed", "error": error_msg, "traceback": tb}


# ---------------------------------------------------------------------------
# ARQ startup / shutdown hooks
# ---------------------------------------------------------------------------

async def startup(ctx: dict[str, Any]) -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    ctx["mongo_client"] = client
    ctx["db"] = client[settings.mongodb_db_name]


async def shutdown(ctx: dict[str, Any]) -> None:
    if "mongo_client" in ctx:
        ctx["mongo_client"].close()


class WorkerSettings:
    functions = [run_ingest_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings_from_dsn = settings.redis_url
    max_jobs = 4
    job_timeout = 600  # 10 minutes per job
