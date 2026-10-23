from app.config import Settings
from app.transcribe.client import Transcriber
from app.transcribe.mock import MockTranscriber
from app.transcribe.openrouter import OpenRouterTranscriber


def build_transcriber(settings: Settings) -> Transcriber:
    if settings.is_transcribe_mock:
        return MockTranscriber()
    return OpenRouterTranscriber(settings)
