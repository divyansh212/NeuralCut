"""Mock implementations (default). Run the whole pipeline with zero API keys.
Real generation is a matter of swapping these for the live adapters.
"""

import struct
import wave

from PIL import Image, ImageDraw

from .base import ScriptProvider, ImageProvider, VoiceProvider


class ScriptMock(ScriptProvider):
    def generate(self, prompt):
        return [
            {"scene": 1, "narration": f"Scene one opens on {prompt}.", "visual_desc": f"{prompt}, wide cinematic shot"},
            {"scene": 2, "narration": "Scene two builds the moment.", "visual_desc": f"{prompt}, close-up detail"},
            {"scene": 3, "narration": "Scene three brings it home.", "visual_desc": f"{prompt}, sweeping finale"},
        ]


class ImageMock(ImageProvider):
    def generate(self, visual_desc, out_path):
        # A simple captioned placeholder frame (1280x720) instead of a flat fill,
        # so the rendered MP4 actually shows the scene description.
        img = Image.new("RGB", (1280, 720), (18, 14, 30))
        d = ImageDraw.Draw(img)
        for y in range(720):
            shade = int(10 + 28 * (y / 720))
            d.line([(0, y), (1280, y)], fill=(shade, int(shade * 0.7), int(shade * 1.3)))
        d.text((60, 620), visual_desc[:90].upper(), fill=(216, 184, 134))
        img.save(out_path)
        return out_path


class VoiceMock(VoiceProvider):
    def generate(self, narration, out_path):
        # 2s of silence so pipeline timing is realistic.
        with wave.open(out_path, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            for _ in range(32000):
                w.writeframes(struct.pack("<h", 0))
        return out_path
