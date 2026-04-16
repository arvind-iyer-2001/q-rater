import pytest
from app.processing.summarizer import StructuredSummarizer
from app.processing.multimodal import AnalysisResult


def test_build_embed_text(sample_raw_media):
    summarizer = StructuredSummarizer()
    analysis = AnalysisResult(
        one_liner="Classic 80s pop song by Rick Astley",
        detailed_summary="A music video featuring the iconic Never Gonna Give You Up.",
        key_topics=["music", "pop", "80s"],
        tags=["rick astley", "pop", "classic"],
    )
    sample_raw_media.raw_transcript = "Never gonna give you up"
    text = summarizer.build_embed_text(analysis, sample_raw_media)
    assert "Rick Astley" in text or "rick astley" in text.lower()
    assert "music" in text


def test_build_document(sample_raw_media):
    summarizer = StructuredSummarizer()
    analysis = AnalysisResult(
        one_liner="Test one liner",
        detailed_summary="Test summary",
        key_topics=["test"],
        tags=["tag1"],
        sentiment="positive",
        content_type="music",
        language="en",
        quality_score=0.9,
    )
    sample_raw_media.raw_transcript = ""
    embeddings = {"combined": [0.1] * 1024, "summary_only": [0.2] * 1024}

    doc = summarizer.build_document(sample_raw_media, analysis, embeddings, job_id="job-123")

    assert doc.source == "youtube"
    assert doc.url == sample_raw_media.url
    assert doc.summary.one_liner == "Test one liner"
    assert doc.summary.quality_score == 0.9
    assert doc.embeddings.combined == [0.1] * 1024
    assert doc.status == "complete"
    assert doc.job_id == "job-123"
