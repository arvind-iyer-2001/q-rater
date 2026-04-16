from app.ingestion.base import AbstractIngester, RawMedia
from app.ingestion.youtube import YouTubeIngester
from app.ingestion.instagram import InstagramIngester
from app.utils.url_parser import detect_platform


class IngestDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, AbstractIngester] = {
            "youtube": YouTubeIngester(),
            "instagram": InstagramIngester(),
        }

    async def ingest(self, url: str, content_id: str) -> RawMedia:
        platform = detect_platform(url)
        if platform == "unknown":
            raise ValueError(f"Unsupported URL platform: {url}")
        handler = self._handlers[platform]
        return await handler.ingest(url, content_id)
