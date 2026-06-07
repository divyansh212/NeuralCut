"""Live implementations. Switching to real generation is exactly: implement
these three, set PROVIDER_MODE=live, supply keys. Nothing else changes.

The image provider here is wired to a PyTorch (diffusers) Stable Diffusion
pipeline so generation runs on your own GPU/CPU with no per-image API cost.
Script -> an LLM (OpenAI). Voice -> a TTS API (ElevenLabs). Both left as
clearly-marked TODOs with the request shape ready.
"""

import os

from .base import ScriptProvider, ImageProvider, VoiceProvider


class ScriptLive(ScriptProvider):
    def generate(self, prompt):
        # TODO: call your LLM (e.g. OpenAI) and parse into
        #   [{"scene": int, "narration": str, "visual_desc": str}, ...]
        #
        # from openai import OpenAI
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # resp = client.chat.completions.create(... ask for JSON scene list ...)
        # return json.loads(resp.choices[0].message.content)["scenes"]
        raise NotImplementedError("Implement ScriptLive.generate")


class ImageLive(ImageProvider):
    """PyTorch / diffusers Stable Diffusion. The model is loaded lazily once and
    cached on the instance so repeated scenes in a job reuse the warm pipeline.
    Requires: torch, diffusers, transformers, accelerate (see pyproject extras).
    """

    _pipe = None

    def _load(self):
        if ImageLive._pipe is not None:
            return ImageLive._pipe
        import torch
        from diffusers import StableDiffusionPipeline

        model_id = os.getenv("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)
        pipe = pipe.to(device)
        if device == "cpu":
            pipe.enable_attention_slicing()
        ImageLive._pipe = pipe
        return pipe

    def generate(self, visual_desc, out_path):
        pipe = self._load()
        steps = int(os.getenv("SD_STEPS", "25"))
        image = pipe(visual_desc, num_inference_steps=steps, height=576, width=1024).images[0]
        image = image.resize((1280, 720))
        image.save(out_path)
        return out_path


class VoiceLive(VoiceProvider):
    def generate(self, narration, out_path):
        # TODO: call your TTS API (e.g. ElevenLabs), write audio bytes to out_path.
        #
        # import requests
        # r = requests.post(url, headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
        #                   json={"text": narration})
        # with open(out_path, "wb") as f: f.write(r.content)
        raise NotImplementedError("Implement VoiceLive.generate")
