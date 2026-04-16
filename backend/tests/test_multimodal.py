import json
from app.processing.multimodal import OllamaMultiModalAnalyzer


def test_parse_response_valid_json():
    raw = json.dumps({
        "one_liner": "A great tutorial on Python async.",
        "detailed_summary": "This video covers asyncio basics.",
        "key_topics": ["python", "asyncio"],
        "tags": ["python", "tutorial"],
        "sentiment": "positive",
        "content_type": "tutorial",
        "language": "en",
        "quality_score": 0.85,
    })
    result = OllamaMultiModalAnalyzer._parse_response(raw)
    assert result.one_liner == "A great tutorial on Python async."
    assert result.quality_score == 0.85
    assert "python" in result.key_topics


def test_parse_response_markdown_fenced():
    raw = '```json\n{"one_liner": "Test", "detailed_summary": "Desc", "key_topics": [], "tags": [], "sentiment": "neutral", "content_type": "general", "language": "en", "quality_score": 0.5}\n```'
    result = OllamaMultiModalAnalyzer._parse_response(raw)
    assert result.one_liner == "Test"


def test_parse_response_fallback():
    result = OllamaMultiModalAnalyzer._parse_response("Not valid JSON at all.")
    assert result.one_liner == "Content analysis unavailable"
