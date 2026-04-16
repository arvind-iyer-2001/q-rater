from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class MediaMetadata(BaseModel):
    title: str = ""
    author: str = ""
    channel: str = ""
    published_at: Optional[datetime] = None
    duration_seconds: int = 0
    view_count: int = 0
    like_count: int = 0
    thumbnail_url: str = ""


class RawContent(BaseModel):
    transcript: str = ""
    captions_raw: str = ""
    comments: list[dict] = Field(default_factory=list)
    description: str = ""


class ContentSummary(BaseModel):
    one_liner: str = ""
    detailed_summary: str = ""
    key_topics: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    content_type: str = "general"
    language: str = "en"
    quality_score: float = 0.0
    tags: list[str] = Field(default_factory=list)


class ContentEmbeddings(BaseModel):
    combined: list[float] = Field(default_factory=list)
    summary_only: list[float] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Primary documents
# ---------------------------------------------------------------------------

class ContentDocument(BaseModel):
    content_id: str = Field(default_factory=_uuid)
    source: Literal["youtube", "instagram"]
    url: str
    platform_id: str = ""

    metadata: MediaMetadata = Field(default_factory=MediaMetadata)
    raw: RawContent = Field(default_factory=RawContent)
    summary: ContentSummary = Field(default_factory=ContentSummary)
    embeddings: ContentEmbeddings = Field(default_factory=ContentEmbeddings)

    job_id: str = ""
    status: Literal["pending", "processing", "complete", "failed"] = "pending"
    error: Optional[str] = None
    progress: int = 0  # 0-100

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class UserProfile(BaseModel):
    user_id: str = Field(default_factory=_uuid)
    interests: list[str] = Field(default_factory=list)
    interest_embedding: list[float] = Field(default_factory=list)
    viewed_content_ids: list[str] = Field(default_factory=list)
    liked_content_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    url: str


class IngestResponse(BaseModel):
    job_id: str
    content_id: str
    status: str = "pending"


class JobStatusResponse(BaseModel):
    job_id: str
    content_id: str
    status: str
    progress: int
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    source_filter: Optional[Literal["youtube", "instagram"]] = None
    content_type_filter: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)
    user_id: Optional[str] = None


class SearchResult(BaseModel):
    content_id: str
    url: str
    source: str
    score: float
    metadata: MediaMetadata
    summary: ContentSummary


class SearchResponse(BaseModel):
    answer: str
    sources: list[SearchResult]


class RecommendationResponse(BaseModel):
    items: list[SearchResult]


class UpdateInterestsRequest(BaseModel):
    interests: list[str]
