from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from app.config import get_settings

settings = get_settings()

_model = None


def _get_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model(settings.whisper_model_size, device=settings.whisper_device)
    return _model


class WhisperTranscriber:
    async def transcribe(self, audio_path: Optional[Path]) -> str:
        if audio_path is None or not audio_path.exists():
            return ""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._transcribe_sync, audio_path)
        return result

    @staticmethod
    def _transcribe_sync(audio_path: Path) -> str:
        model = _get_model()
        result = model.transcribe(str(audio_path), fp16=False, verbose=False)
        return result.get("text", "").strip()
