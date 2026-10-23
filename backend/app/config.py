from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Interview Copilot"
    database_url: str = "postgresql+asyncpg://copilot:copilot@db:5432/copilot"

    llm_provider: Literal["openrouter", "mock"] = "mock"
    llm_model: str = "deepseek/deepseek-v3.2"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    llm_temperature: float = 0.2
    llm_max_tokens: int = 8000
    llm_request_timeout: float = 120.0

    transcribe_provider: Literal["openrouter", "mock"] = "mock"
    transcribe_model: str = "openai/whisper-large-v3"
    max_upload_mb: int = 200
    transcribe_chunk_seconds: int = 240

    max_review_iterations: int = 1
    agent_use_tools: bool = False
    agent_max_tool_turns: int = 4

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72

    cors_origins: list[str] = ["*"]

    @property
    def is_mock(self) -> bool:
        return self.llm_provider == "mock" or not self.openrouter_api_key

    @property
    def is_transcribe_mock(self) -> bool:
        return self.transcribe_provider == "mock" or not self.openrouter_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
