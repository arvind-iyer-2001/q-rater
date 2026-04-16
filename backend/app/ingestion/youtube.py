from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import yt_dlp

from app.config import get_settings
from app.ingestion.base import AbstractIngester, RawMedia
from app.utils.file_utils import get_media_dir

settings = get_settings()


class YouTubeIngester(AbstractIngester):
    async def ingest(self, url: str, content_id: str) -> RawMedia:
        media_dir = get_media_dir(content_id)
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, self._download_sync, url, content_id, media_dir)
        return raw

    def _download_sync(self, url: str, content_id: str, media_dir: Path) -> RawMedia:
        video_path: Path | None = None
        audio_path: Path | None = None
        captions_raw = ""
        metadata: dict[str, Any] = {}
        platform_id = ""

        ydl_opts: dict[str, Any] = {
            "outtmpl": str(media_dir / "%(id)s.%(ext)s"),
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
            "merge_output_format": "mp4",
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "writecomments": True,
            "getcomments": True,
            "max_comments": ["100"],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "0",
                    "nopostoverwrites": True,
                },
            ],
            "quiet": True,
            "no_warnings": True,
            "max_filesize": 500 * 1024 * 1024,  # 500 MB cap
            "match_filter": self._duration_filter,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if info is None:
            raise ValueError(f"Could not extract info from {url}")

        platform_id = info.get("id", "")

        # Locate downloaded files
        for f in media_dir.iterdir():
            if f.suffix == ".mp4":
                video_path = f
            elif f.suffix == ".wav":
                audio_path = f

        # Extract captions from .vtt/.srt files
        for f in media_dir.iterdir():
            if f.suffix in (".vtt", ".srt"):
                captions_raw = _strip_subtitle_markup(f.read_text(errors="replace"))
                break

        # Build metadata
        metadata = {
            "title": info.get("title", ""),
            "author": info.get("uploader", ""),
            "channel": info.get("channel", info.get("uploader", "")),
            "published_at": _parse_upload_date(info.get("upload_date")),
            "duration_seconds": int(info.get("duration") or 0),
            "view_count": int(info.get("view_count") or 0),
            "like_count": int(info.get("like_count") or 0),
            "thumbnail_url": info.get("thumbnail", ""),
        }

        # Parse comments
        raw_comments = info.get("comments") or []
        comments = [
            {
                "author": c.get("author", ""),
                "text": c.get("text", ""),
                "likes": c.get("like_count", 0),
            }
            for c in raw_comments[:100]
            if isinstance(c, dict)
        ]

        return RawMedia(
            content_id=content_id,
            source="youtube",
            url=url,
            platform_id=platform_id,
            video_path=video_path,
            audio_path=audio_path,
            captions_raw=captions_raw,
            description=info.get("description", ""),
            comments=comments,
            metadata=metadata,
        )

    @staticmethod
    def _duration_filter(info: dict, **_) -> str | None:
        duration = info.get("duration") or 0
        max_dur = settings.max_video_duration_seconds
        if duration > max_dur:
            return f"Video is {duration}s, exceeds limit of {max_dur}s"
        return None


def _strip_subtitle_markup(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\d{2}:\d{2}:\d{2}[\.,]\d{3} --> .*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"WEBVTT.*?\n\n", "", text, flags=re.DOTALL)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for ln in lines:
        if ln not in seen:
            seen.add(ln)
            unique.append(ln)
    return " ".join(unique)


def _parse_upload_date(date_str: str | None) -> str | None:
    if not date_str or len(date_str) != 8:
        return None
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
