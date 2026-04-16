from typing import Literal
from urllib.parse import urlparse


Platform = Literal["youtube", "instagram", "unknown"]


def detect_platform(url: str) -> Platform:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().replace("www.", "")

    if host in ("youtube.com", "youtu.be", "m.youtube.com"):
        return "youtube"
    if host in ("instagram.com", "m.instagram.com"):
        return "instagram"
    return "unknown"
