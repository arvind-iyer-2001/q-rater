import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def sample_raw_media():
    from pathlib import Path
    from app.ingestion.base import RawMedia

    return RawMedia(
        content_id="test-content-id",
        source="youtube",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        platform_id="dQw4w9WgXcQ",
        video_path=None,
        audio_path=None,
        captions_raw="Never gonna give you up, never gonna let you down",
        description="Rick Astley - Never Gonna Give You Up",
        comments=[
            {"author": "user1", "text": "Classic!", "likes": 100},
        ],
        metadata={
            "title": "Never Gonna Give You Up",
            "author": "RickAstleyVEVO",
            "channel": "RickAstleyVEVO",
            "published_at": "2009-10-25",
            "duration_seconds": 213,
            "view_count": 1400000000,
            "like_count": 15000000,
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        },
    )
