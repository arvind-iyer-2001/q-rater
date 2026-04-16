from fastapi import APIRouter

from app.api.ingest import router as ingest_router
from app.api.search import router as search_router
from app.api.content import router as content_router

api_router = APIRouter(prefix="/api")

api_router.include_router(ingest_router)
api_router.include_router(search_router)
api_router.include_router(content_router)
