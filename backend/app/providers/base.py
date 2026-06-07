from abc import ABC, abstractmethod


class ScriptProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> list[dict]:
        """Return [{scene, narration, visual_desc}, ...]"""
        ...


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, visual_desc: str, out_path: str) -> str:
        """Write an image to out_path, return the path."""
        ...


class VoiceProvider(ABC):
    @abstractmethod
    def generate(self, narration: str, out_path: str) -> str:
        """Write audio to out_path, return the path."""
        ...
