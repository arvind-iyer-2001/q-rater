import os
import shutil
from pathlib import Path

from app.config import get_settings

settings = get_settings()


def get_media_dir(content_id: str) -> Path:
    base = Path(settings.media_temp_dir)
    media_dir = base / content_id
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir


def cleanup_media_dir(content_id: str) -> None:
    media_dir = Path(settings.media_temp_dir) / content_id
    if media_dir.exists():
        shutil.rmtree(media_dir, ignore_errors=True)


def extract_keyframes(
    video_path: Path,
    num_frames: int = 50,
) -> list[bytes]:
    """Extract `num_frames` evenly spaced JPEG keyframes from a video file.
    Works correctly for any duration — a 10s Reel and a 10min YouTube video
    both yield exactly `num_frames` samples spread across the full timeline."""
    try:
        import cv2
    except ImportError:
        return []

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        cap.release()
        return []

    # Clamp so we don't request more frames than the video has
    num_frames = min(num_frames, total_frames)

    # Evenly space sample indices across [0, total_frames)
    indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    frames: list[bytes] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        ret2, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ret2:
            frames.append(bytes(buf))

    cap.release()
    return frames


def ensure_temp_dir() -> None:
    os.makedirs(settings.media_temp_dir, exist_ok=True)
