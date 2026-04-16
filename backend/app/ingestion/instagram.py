from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.ingestion.base import AbstractIngester, RawMedia
from app.utils.file_utils import get_media_dir

settings = get_settings()


class InstagramIngester(AbstractIngester):
    async def ingest(self, url: str, content_id: str) -> RawMedia:
        media_dir = get_media_dir(content_id)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, url, content_id, media_dir)

    def _download_sync(self, url: str, content_id: str, media_dir: Path) -> RawMedia:
        try:
            import instaloader
        except ImportError as exc:
            raise RuntimeError("instaloader is not installed") from exc

        shortcode = _extract_shortcode(url)
        if not shortcode:
            raise ValueError(f"Could not extract Instagram shortcode from {url}")

        loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=True,
            save_metadata=False,
            compress_json=False,
            dirname_pattern=str(media_dir),
            filename_pattern=content_id,
            quiet=True,
        )

        if settings.instagram_session_id:
            loader.context._session.cookies.set(
                "sessionid", settings.instagram_session_id, domain=".instagram.com"
            )
        if settings.instagram_csrf_token:
            loader.context._session.cookies.set(
                "csrftoken", settings.instagram_csrf_token, domain=".instagram.com"
            )

        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=media_dir)

        # Locate video file
        video_path: Path | None = None
        audio_path: Path | None = None
        for f in media_dir.iterdir():
            if f.suffix == ".mp4":
                video_path = f
                break

        # Try to extract audio via ffmpeg if video was downloaded
        if video_path:
            audio_path = _extract_audio(video_path)

        # Caption text (Instagram uses the post caption as "description")
        caption = post.caption or ""

        # Comments
        comments: list[dict] = []
        try:
            for comment in post.get_comments():
                comments.append({
                    "author": comment.owner.username,
                    "text": comment.text,
                    "likes": getattr(comment, "likes_count", 0),
                })
                if len(comments) >= 100:
                    break
        except Exception:
            pass

        metadata: dict[str, Any] = {
            "title": caption[:100] if caption else "",
            "author": post.owner_username,
            "channel": post.owner_profile.full_name if post.owner_profile else "",
            "published_at": post.date_utc.isoformat() if post.date_utc else None,
            "duration_seconds": int(post.video_duration or 0),
            "view_count": int(post.video_view_count or 0),
            "like_count": int(post.likes or 0),
            "thumbnail_url": post.url,
        }

        return RawMedia(
            content_id=content_id,
            source="instagram",
            url=url,
            platform_id=shortcode,
            video_path=video_path,
            audio_path=audio_path,
            captions_raw="",
            description=caption,
            comments=comments,
            metadata=metadata,
        )


def _extract_shortcode(url: str) -> str | None:
    patterns = [
        r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)",
        r"instagram\.com/reels/([A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def _extract_audio(video_path: Path) -> Path | None:
    try:
        import ffmpeg
        audio_path = video_path.with_suffix(".wav")
        (
            ffmpeg
            .input(str(video_path))
            .output(str(audio_path), acodec="pcm_s16le", ac=1, ar="16000")
            .overwrite_output()
            .run(quiet=True)
        )
        return audio_path if audio_path.exists() else None
    except Exception:
        return None
