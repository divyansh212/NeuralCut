"""Provider interfaces.

Every external generative call goes through one of these. The orchestrator
never imports OpenAI / Anthropic / Replicate / etc. directly — it depends
on the interface. That's how mock mode works.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class SceneSpec:
    idx: int
    narration: str
    visual_prompt: str
    duration_s: float = 4.0


class ScriptProvider(ABC):
    """Turns a free-form prompt + style into a list of scenes."""

    @abstractmethod
    async def generate_scenes(self, prompt: str, style: dict) -> list[SceneSpec]: ...

    @abstractmethod
    async def stream_thoughts(
        self, prompt: str, style: dict
    ) -> AsyncIterator[str]:  # noqa: E501
        """Optional: yield reasoning tokens for the live trace UI."""
        ...


class ImageProvider(ABC):
    """Generates a still image for one scene. Returns local file path."""

    @abstractmethod
    async def generate(self, prompt: str, aspect: str, out_path: str) -> str: ...


class TTSProvider(ABC):
    """Generates spoken audio for one scene. Returns local file path."""

    @abstractmethod
    async def synthesize(
        self, text: str, voice_id: str | None, out_path: str
    ) -> str: ...
