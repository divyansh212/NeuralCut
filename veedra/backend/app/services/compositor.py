"""ffmpeg-based scene compositor.

Each scene is one image + one voice clip. We render each scene as a
short clip (image still + audio), then concat. Transitions are kept
simple (xfade is gated behind a flag — slow on long videos).
"""

from __future__ import annotations
import asyncio
import os
import shlex
import tempfile
from dataclasses import dataclass


@dataclass
class SceneClip:
    image_path: str
    voice_path: str
    duration_s: float


async def _run(cmd: str) -> None:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{err.decode(errors='ignore')[:2000]}")


async def render_scene(clip: SceneClip, out_path: str, size: tuple[int, int]) -> str:
    w, h = size
    cmd = (
        f"ffmpeg -y -loop 1 -i {shlex.quote(clip.image_path)} "
        f"-i {shlex.quote(clip.voice_path)} "
        f"-c:v libx264 -tune stillimage -pix_fmt yuv420p "
        f"-vf scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},fps=30 "
        f"-c:a aac -b:a 160k -shortest -t {clip.duration_s} "
        f"{shlex.quote(out_path)}"
    )
    await _run(cmd)
    return out_path


async def concat_scenes(scene_paths: list[str], out_path: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in scene_paths:
            f.write(f"file {shlex.quote(p)}\n")
        list_path = f.name
    cmd = (
        f"ffmpeg -y -f concat -safe 0 -i {shlex.quote(list_path)} "
        f"-c copy {shlex.quote(out_path)}"
    )
    try:
        await _run(cmd)
    finally:
        os.unlink(list_path)
    return out_path


async def make_thumbnail(video_path: str, out_path: str) -> str:
    cmd = (
        f"ffmpeg -y -i {shlex.quote(video_path)} -ss 00:00:01 -vframes 1 "
        f"{shlex.quote(out_path)}"
    )
    await _run(cmd)
    return out_path


def aspect_size(aspect: str) -> tuple[int, int]:
    return {
        "16:9": (1280, 720),
        "9:16": (720, 1280),
        "1:1": (1024, 1024),
    }.get(aspect, (1280, 720))
