from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

import ollama

from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are a content intelligence analyst. You will analyze video content — including transcript, captions, description, viewer comments, and key video frames — to produce a structured analysis.

Always respond with a single JSON object matching exactly this schema:
{
  "one_liner": "<30-word summary>",
  "detailed_summary": "<2-4 paragraph detailed summary>",
  "key_topics": ["topic1", "topic2", ...],
  "tags": ["tag1", "tag2", ...],
  "sentiment": "positive | negative | neutral | mixed",
  "content_type": "tutorial | review | entertainment | news | vlog | music | sports | cooking | travel | tech | education | general",
  "language": "<ISO 639-1 code, e.g. en>",
  "quality_score": <float 0.0-1.0 reflecting content quality and depth>
}

Be concise, factual, and objective. Base your analysis strictly on the provided content. Output only the JSON object with no surrounding text."""


@dataclass
class AnalysisResult:
    one_liner: str = ""
    detailed_summary: str = ""
    key_topics: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    content_type: str = "general"
    language: str = "en"
    quality_score: float = 0.5


class OllamaMultiModalAnalyzer:
    def __init__(self) -> None:
        self._client: ollama.AsyncClient | None = None

    def _get_client(self) -> ollama.AsyncClient:
        if self._client is None:
            self._client = ollama.AsyncClient(host=settings.ollama_base_url)
        return self._client

    async def analyze(
        self,
        transcript: str,
        captions: Optional[str],
        description: str,
        comments: list[dict],
        frames: list[bytes],
    ) -> AnalysisResult:
        prompt = self._build_prompt(transcript, captions, description, comments)

        # Build the user message; attach frames as images if the model supports vision.
        # Ollama accepts raw bytes in the `images` list — it handles base64 encoding internally.
        user_message: dict = {"role": "user", "content": prompt}
        if frames:
            user_message["images"] = list(frames[:8])

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            user_message,
        ]

        try:
            response = await self._get_client().chat(
                model=settings.ollama_model,
                messages=messages,
                options={"temperature": 0.1},  # low temp for deterministic JSON
            )
            raw_text = response.message.content or ""
        except Exception as exc:
            # If the model doesn't support vision, retry with text only
            if frames and ("vision" in str(exc).lower() or "image" in str(exc).lower()):
                text_only_msg = {"role": "user", "content": prompt}
                response = await self._get_client().chat(
                    model=settings.ollama_model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, text_only_msg],
                    options={"temperature": 0.1},
                )
                raw_text = response.message.content or ""
            else:
                raise

        return self._parse_response(raw_text)

    @staticmethod
    def _build_prompt(
        transcript: str,
        captions: Optional[str],
        description: str,
        comments: list[dict],
    ) -> str:
        parts = ["Analyze the following video content:\n"]

        if description:
            parts.append(f"## Description\n{description[:2000]}\n")

        if transcript:
            parts.append(f"## Transcript\n{transcript[:6000]}\n")
        elif captions:
            parts.append(f"## Captions\n{captions[:4000]}\n")

        if comments:
            comment_text = "\n".join(
                f"- {c.get('author', 'user')}: {c.get('text', '')}"
                for c in comments[:30]
            )
            parts.append(f"## Top Comments\n{comment_text}\n")

        parts.append("\nReturn the structured JSON analysis.")
        return "\n".join(parts)

    @staticmethod
    def _parse_response(text: str) -> AnalysisResult:
        # Strip markdown code fences if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            obj_match = re.search(r"\{.*\}", text, re.DOTALL)
            if obj_match:
                text = obj_match.group(0)

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return AnalysisResult(
                one_liner="Content analysis unavailable",
                detailed_summary=text[:500] if text else "",
            )

        return AnalysisResult(
            one_liner=str(data.get("one_liner", ""))[:200],
            detailed_summary=str(data.get("detailed_summary", "")),
            key_topics=list(data.get("key_topics", []))[:20],
            tags=list(data.get("tags", []))[:30],
            sentiment=str(data.get("sentiment", "neutral")),
            content_type=str(data.get("content_type", "general")),
            language=str(data.get("language", "en")),
            quality_score=float(data.get("quality_score", 0.5)),
        )
