from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RawMedia:
    content_id: str
    source: str  # "youtube" | "instagram"
    url: str
    platform_id: str = ""
    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    captions_raw: str = ""
    description: str = ""
    comments: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class AbstractIngester(ABC):
    @abstractmethod
    async def ingest(self, url: str, content_id: str) -> RawMedia:
        ...
