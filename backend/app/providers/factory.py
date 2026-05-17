"""Selects mock vs live providers based on PROVIDER_MODE."""

from __future__ import annotations
from app.config import get_settings
from app.providers.base import ScriptProvider, ImageProvider, TTSProvider


def script_provider() -> ScriptProvider:
    s = get_settings()
    if s.provider_mode != "live":
        from app.providers.mock import MockScriptProvider
        return MockScriptProvider()
    if s.llm_provider == "openai":
        from app.providers.live import OpenAIScriptProvider
        return OpenAIScriptProvider()
    from app.providers.live import AnthropicScriptProvider
    return AnthropicScriptProvider()


def image_provider() -> ImageProvider:
    s = get_settings()
    if s.provider_mode != "live":
        from app.providers.mock import MockImageProvider
        return MockImageProvider()
    from app.providers.live import ReplicateImageProvider
    return ReplicateImageProvider()


def tts_provider() -> TTSProvider:
    s = get_settings()
    if s.provider_mode != "live":
        from app.providers.mock import MockTTSProvider
        return MockTTSProvider()
    from app.providers.live import ElevenLabsTTSProvider
    return ElevenLabsTTSProvider()
