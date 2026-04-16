from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ingestion.base import RawMedia
from app.processing.embedder import VoyageEmbedder
from app.processing.multimodal import OllamaMultiModalAnalyzer
from app.processing.summarizer import StructuredSummarizer
from app.processing.transcriber import WhisperTranscriber
from app.storage.models import ContentDocument
from app.storage.mongo import update_job_status
from app.utils.file_utils import extract_keyframes, cleanup_media_dir


class ProcessingPipeline:
    def __init__(self) -> None:
        self.transcriber = WhisperTranscriber()
        self.analyzer = OllamaMultiModalAnalyzer()
        self.embedder = VoyageEmbedder()
        self.summarizer = StructuredSummarizer()

    async def process(
        self,
        raw: RawMedia,
        job_id: str,
        db: AsyncIOMotorDatabase,
    ) -> ContentDocument:
        try:
            # Step 1: Transcribe audio (20%)
            await update_job_status(db, job_id, "processing", progress=10)
            transcript = await self.transcriber.transcribe(raw.audio_path)
            # Attach transcript to raw so summarizer can access it
            raw.raw_transcript = transcript  # type: ignore[attr-defined]
            await update_job_status(db, job_id, "processing", progress=30)

            # Step 2: Extract keyframes for vision context (40%)
            frames: list[bytes] = []
            if raw.video_path and raw.video_path.exists():
                frames = extract_keyframes(raw.video_path, num_frames=50)
            await update_job_status(db, job_id, "processing", progress=50)

            # Step 3: Multi-modal LLM analysis (70%)
            analysis = await self.analyzer.analyze(
                transcript=transcript,
                captions=raw.captions_raw or None,
                description=raw.description,
                comments=raw.comments[:50],
                frames=frames,
            )
            await update_job_status(db, job_id, "processing", progress=70)

            # Step 4: Generate embeddings (90%)
            embed_text = self.summarizer.build_embed_text(analysis, raw)
            embeddings = await self.embedder.embed_pair(
                combined_text=embed_text,
                summary_text=analysis.detailed_summary or analysis.one_liner,
            )
            await update_job_status(db, job_id, "processing", progress=90)

            # Step 5: Assemble ContentDocument
            doc = self.summarizer.build_document(raw, analysis, embeddings, job_id)
            doc.content_id = raw.content_id

            return doc

        finally:
            # Always clean up temp media files
            cleanup_media_dir(raw.content_id)
