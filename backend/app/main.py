from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.storage.mongo import ensure_indexes, get_database
from app.utils.file_utils import ensure_temp_dir

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Q-Rater API")
    ensure_temp_dir()
    db = get_database()
    await ensure_indexes(db)
    logger.info("MongoDB indexes ensured")
    yield
    logger.info("Shutting down Q-Rater API")
    from app.storage.mongo import close_client
    await close_client()


app = FastAPI(
    title="Q-Rater",
    description="Content intelligence pipeline for YouTube and Instagram videos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "q-rater"}
