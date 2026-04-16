from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4"

    # MongoDB Atlas
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "q_rater"
    mongodb_collection_content: str = "content"
    mongodb_collection_users: str = "users"
    mongodb_vector_index_name: str = "content_vector_index"

    # Voyage AI
    voyage_api_key: str = ""
    embedding_model: str = "voyage-large-2-instruct"
    embedding_dimension: int = 1024

    # Redis / ARQ
    redis_url: str = "redis://localhost:6379"

    # Whisper
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"

    # Media
    media_temp_dir: str = "/tmp/q_rater_media"
    max_video_duration_seconds: int = 600

    # Instagram
    instagram_session_id: str = ""
    instagram_csrf_token: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
