from app.config import Settings
from app.llm.client import LLMClient
from app.llm.mock import MockLLMClient
from app.llm.openrouter import OpenRouterClient


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.is_mock:
        return MockLLMClient()
    return OpenRouterClient(settings)
