"""Mock providers. Free, fast, deterministic. Default when PROVIDER_MODE=mock."""

from __future__ import annotations
import asyncio
import os
import wave
import struct
import math
import random
from typing import AsyncIterator

from PIL import Image, ImageDraw, ImageFont

from app.providers.base import ScriptProvider, ImageProvider, TTSProvider, SceneSpec


# ─── Script: rule-based scene decomposition ──────────────────────────
class MockScriptProvider(ScriptProvider):
    async def generate_scenes(self, prompt: str, style: dict) -> list[SceneSpec]:
        await asyncio.sleep(0.3)
        n = int(style.get("scenes") or 4)
        tone = style.get("tone", "friendly")
        scenes: list[SceneSpec] = []
        for i in range(n):
            scenes.append(SceneSpec(
                idx=i,
                narration=(
                    f"[Scene {i+1}/{n} · {tone}] "
                    f"{prompt.strip().rstrip('.')}. "
                    f"Part {i+1} of the story."
                ),
                visual_prompt=(
                    f"Cinematic shot illustrating: {prompt}. "
                    f"Beat {i+1}. Style: {style.get('visual_style','editorial photography')}."
                ),
                duration_s=4.0,
            ))
        return scenes

    async def stream_thoughts(self, prompt: str, style: dict) -> AsyncIterator[str]:
        chunks = [
            "Reading the prompt and identifying core message...",
            f"Picking {style.get('scenes',4)}-scene structure for pacing.",
            "Drafting narration with a friendly explainer voice...",
            "Suggesting per-scene visuals that build a clear arc.",
            "Done — handing off to the visual + voice agents.",
        ]
        for c in chunks:
            await asyncio.sleep(0.25)
            yield c


# ─── Image: PIL-generated placeholder cards ──────────────────────────
class MockImageProvider(ImageProvider):
    async def generate(self, prompt: str, aspect: str, out_path: str) -> str:
        sizes = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}
        w, h = sizes.get(aspect, (1280, 720))

        # Deterministic colors from the prompt
        seed = sum(ord(c) for c in prompt)
        rng = random.Random(seed)
        bg = (rng.randint(40, 100), rng.randint(40, 100), rng.randint(80, 160))
        accent = (rng.randint(160, 240), rng.randint(160, 240), rng.randint(200, 255))

        img = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(img)

        # Gradient overlay (cheap)
        for y in range(h):
            t = y / h
            r = int(bg[0] * (1 - t) + accent[0] * t * 0.25)
            g = int(bg[1] * (1 - t) + accent[1] * t * 0.25)
            b = int(bg[2] * (1 - t) + accent[2] * t * 0.25)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36
            )
        except OSError:
            font = ImageFont.load_default()

        # Wrap prompt onto the card
        text = prompt[:140] + ("..." if len(prompt) > 140 else "")
        margin = 60
        draw.text((margin, h - 200), "VEEDRA · scene preview",
                  font=font, fill=(255, 255, 255))
        draw.text((margin, h - 140), text, font=font, fill=accent)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        img.save(out_path, "PNG")
        await asyncio.sleep(0.2)
        return out_path


# ─── TTS: synthesized sine-wave with silence (placeholder audio) ─────
class MockTTSProvider(TTSProvider):
    async def synthesize(
        self, text: str, voice_id: str | None, out_path: str
    ) -> str:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # ~120 wpm reading rate
        words = max(1, len(text.split()))
        duration_s = min(20.0, max(2.0, words / 2.5))
        sample_rate = 22050
        n_frames = int(duration_s * sample_rate)

        with wave.open(out_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            # quiet sine just so the file is valid audio, not absolute silence
            for i in range(n_frames):
                v = int(800 * math.sin(2 * math.pi * 220 * i / sample_rate))
                w.writeframes(struct.pack("<h", v))

        await asyncio.sleep(0.1)
        return out_path
