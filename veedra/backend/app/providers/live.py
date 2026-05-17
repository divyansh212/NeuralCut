"""Live provider adapters. Used when PROVIDER_MODE=live.

Each adapter has the same interface as its mock counterpart so the
orchestrator code stays identical. Replace mock with live by changing
one env var. To plug in another vendor: subclass the base and register
it in factory.py.
"""

from __future__ import annotations
import asyncio
import os
import json
from typing import AsyncIterator

import httpx
import anthropic
from openai import OpenAI

from app.config import get_settings
from app.providers.base import ScriptProvider, ImageProvider, TTSProvider, SceneSpec


_SCRIPT_SYSTEM = """You are Veedra's script director. Given a user prompt and style hints,
return a JSON object with key "scenes": an array of {idx, narration, visual_prompt, duration_s}.
Constraints:
- narration: <=22 words, spoken naturally
- visual_prompt: vivid, specific, includes lighting + composition
- duration_s: 3-6
Output ONLY the JSON. No prose."""


class AnthropicScriptProvider(ScriptProvider):
    def __init__(self) -> None:
        s = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=s.anthropic_api_key)
        self._model = s.llm_model

    async def generate_scenes(self, prompt: str, style: dict) -> list[SceneSpec]:
        n = int(style.get("scenes") or 4)
        user = (
            f"User prompt: {prompt}\n"
            f"Aspect: {style.get('aspect','16:9')}\n"
            f"Tone: {style.get('tone','friendly explainer')}\n"
            f"Number of scenes: {n}\n"
            f"Visual style: {style.get('visual_style','cinematic')}\n"
        )
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=_SCRIPT_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        data = json.loads(text)
        scenes = data["scenes"][:n]
        return [SceneSpec(**s) for s in scenes]

    async def stream_thoughts(self, prompt: str, style: dict) -> AsyncIterator[str]:
        # Use Anthropic streaming to surface partial reasoning to the UI.
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=600,
            system="Narrate, in 4-6 short lines, how you'd structure this video.",
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OpenAIScriptProvider(ScriptProvider):
    def __init__(self) -> None:
        s = get_settings()
        self._client = OpenAI(api_key=s.openai_api_key)
        self._model = "gpt-4o-mini"

    async def generate_scenes(self, prompt: str, style: dict) -> list[SceneSpec]:
        n = int(style.get("scenes") or 4)
        # Run in threadpool — openai sdk is sync
        def _call() -> str:
            r = self._client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SCRIPT_SYSTEM},
                    {"role": "user", "content":
                        f"{prompt}\nstyle: {json.dumps(style)}\nscenes: {n}"},
                ],
            )
            return r.choices[0].message.content or "{}"
        text = await asyncio.to_thread(_call)
        data = json.loads(text)
        return [SceneSpec(**s) for s in data.get("scenes", [])[:n]]

    async def stream_thoughts(self, prompt: str, style: dict) -> AsyncIterator[str]:
        yield "Analyzing prompt..."
        yield "Drafting scenes..."


class ReplicateImageProvider(ImageProvider):
    """Calls Replicate's flux-schnell by default. Swap model_ref to taste."""

    MODEL_REF = "black-forest-labs/flux-schnell"

    async def generate(self, prompt: str, aspect: str, out_path: str) -> str:
        s = get_settings()
        async with httpx.AsyncClient(timeout=120) as http:
            create = await http.post(
                "https://api.replicate.com/v1/predictions",
                headers={"Authorization": f"Bearer {s.replicate_api_token}"},
                json={
                    "version": self.MODEL_REF,
                    "input": {"prompt": prompt, "aspect_ratio": aspect},
                },
            )
            create.raise_for_status()
            pred = create.json()
            url = pred["urls"]["get"]
            for _ in range(60):
                await asyncio.sleep(1.5)
                poll = await http.get(
                    url, headers={"Authorization": f"Bearer {s.replicate_api_token}"}
                )
                pred = poll.json()
                if pred["status"] == "succeeded":
                    img_url = pred["output"][0] if isinstance(pred["output"], list) \
                        else pred["output"]
                    img = await http.get(img_url)
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, "wb") as f:
                        f.write(img.content)
                    return out_path
                if pred["status"] == "failed":
                    raise RuntimeError(f"Replicate failed: {pred.get('error')}")
            raise TimeoutError("Replicate timed out")


class ElevenLabsTTSProvider(TTSProvider):
    DEFAULT_VOICE = "EXAVITQu4vr4xnSDxMaL"  # Bella, public preset

    async def synthesize(self, text: str, voice_id: str | None, out_path: str) -> str:
        s = get_settings()
        vid = voice_id or self.DEFAULT_VOICE
        async with httpx.AsyncClient(timeout=60) as http:
            r = await http.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
                headers={
                    "xi-api-key": s.elevenlabs_api_key,
                    "accept": "audio/mpeg",
                    "content-type": "application/json",
                },
                json={"text": text, "model_id": "eleven_turbo_v2_5"},
            )
            r.raise_for_status()
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(r.content)
        return out_path
