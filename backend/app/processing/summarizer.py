from __future__ import annotations

from datetime import datetime, timezone

from app.ingestion.base import RawMedia
from app.processing.multimodal import AnalysisResult
from app.storage.models import (
    ContentDocument,
    ContentEmbeddings,
    ContentSummary,
    MediaMetadata,
    RawContent,
)


class StructuredSummarizer:
    def build_embed_text(self, analysis: AnalysisResult, raw: RawMedia) -> str:
        """Compose a rich text blob for the combined embedding."""
        parts = [
            analysis.one_liner,
            analysis.detailed_summary,
            " ".join(analysis.key_topics),
            " ".join(analysis.tags),
            raw.metadata.get("title", ""),
            raw.metadata.get("author", ""),
            raw.description[:500],
        ]
        if raw.raw_transcript:
            parts.append(raw.raw_transcript[:2000])
        return "\n".join(p for p in parts if p).strip()

    def build_document(
        self,
        raw: RawMedia,
        analysis: AnalysisResult,
        embeddings: dict[str, list[float]],
        job_id: str,
    ) -> ContentDocument:
        meta = raw.metadata
        published_at: datetime | None = None
        if meta.get("published_at"):
            try:
                published_at = datetime.fromisoformat(str(meta["published_at"]))
            except ValueError:
                pass

        return ContentDocument(
            source=raw.source,
            url=raw.url,
            platform_id=raw.platform_id,
            metadata=MediaMetadata(
                title=str(meta.get("title", "")),
                author=str(meta.get("author", "")),
                channel=str(meta.get("channel", "")),
                published_at=published_at,
                duration_seconds=int(meta.get("duration_seconds", 0)),
                view_count=int(meta.get("view_count", 0)),
                like_count=int(meta.get("like_count", 0)),
                thumbnail_url=str(meta.get("thumbnail_url", "")),
            ),
            raw=RawContent(
                transcript=getattr(raw, "raw_transcript", ""),
                captions_raw=raw.captions_raw,
                comments=raw.comments,
                description=raw.description,
            ),
            summary=ContentSummary(
                one_liner=analysis.one_liner,
                detailed_summary=analysis.detailed_summary,
                key_topics=analysis.key_topics,
                tags=analysis.tags,
                sentiment=analysis.sentiment,
                content_type=analysis.content_type,
                language=analysis.language,
                quality_score=analysis.quality_score,
            ),
            embeddings=ContentEmbeddings(
                combined=embeddings.get("combined", []),
                summary_only=embeddings.get("summary_only", []),
            ),
            job_id=job_id,
            status="complete",
            progress=100,
        )
