"""Agent orchestrator.

Coordinates the multi-agent pipeline that turns a prompt into a video.
Mirrors the Director / Mora multi-agent pattern: each step is a distinct
agent with a single responsibility, and progress is streamed to the UI.

Pipeline:
    1. script_agent   prompt        -> [SceneSpec...]
    2. visual_agent   SceneSpec     -> image file
    3. voice_agent    SceneSpec     -> audio file
    4. compositor     scene clips   -> final mp4
    5. uploader       mp4 + thumb   -> URLs in supabase storage

Each step writes an `agent_events` row and an in-memory bus event so the
SSE endpoint can stream live updates without polling the DB.
"""

from __future__ import annotations
import asyncio
import os
import tempfile
from dataclasses import dataclass, field
from typing import Callable, Awaitable
from uuid import UUID

from app.config import get_settings
from app.providers.base import SceneSpec
from app.providers.factory import script_provider, image_provider, tts_provider
from app.services import compositor
from app.services.storage import upload
from app.services.supabase import pg_conn


# A simple in-process pubsub keyed by job_id. SSE handlers subscribe.
_subscribers: dict[UUID, list[asyncio.Queue]] = {}


def subscribe(job_id: UUID) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(job_id, []).append(q)
    return q


def unsubscribe(job_id: UUID, q: asyncio.Queue) -> None:
    if job_id in _subscribers and q in _subscribers[job_id]:
        _subscribers[job_id].remove(q)


async def _emit(job_id: UUID, step: str, role: str, content: dict) -> None:
    # Persist (so reload still shows trace)
    with pg_conn() as conn, conn.cursor() as cur:
        import json
        cur.execute(
            "insert into agent_events (job_id, step, role, content) "
            "values (%s, %s, %s, %s::jsonb)",
            (str(job_id), step, role, json.dumps(content)),
        )
    # Fan out to live subscribers
    for q in _subscribers.get(job_id, []):
        await q.put({"step": step, "role": role, "content": content})


async def _set_job(
    job_id: UUID,
    status: str | None = None,
    progress: int | None = None,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    import json
    sets: list[str] = []
    vals: list = []
    if status is not None:
        sets.append("status = %s"); vals.append(status)
    if progress is not None:
        sets.append("progress = %s"); vals.append(progress)
    if result is not None:
        sets.append("result = %s::jsonb"); vals.append(json.dumps(result))
    if error is not None:
        sets.append("error = %s"); vals.append(error)
    if not sets:
        return
    vals.append(str(job_id))
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(f"update jobs set {', '.join(sets)} where id = %s", vals)


@dataclass
class _RunContext:
    job_id: UUID
    project_id: UUID
    owner_id: UUID
    prompt: str
    style: dict
    workdir: str = field(default_factory=lambda: tempfile.mkdtemp(prefix="veedra_"))


# ─── Pipeline ────────────────────────────────────────────────────────
async def run_pipeline(
    job_id: UUID, project_id: UUID, owner_id: UUID, prompt: str, style: dict
) -> dict:
    ctx = _RunContext(job_id, project_id, owner_id, prompt, style)
    s = get_settings()
    await _set_job(job_id, status="running", progress=1)

    try:
        # ── 1. script ────────────────────────────────────────────────
        await _emit(job_id, "script", "agent",
                    {"message": "Decomposing prompt into scenes..."})
        scenes = await script_provider().generate_scenes(prompt, style)
        await _persist_scenes(project_id, scenes)
        await _emit(job_id, "script", "agent",
                    {"message": f"Drafted {len(scenes)} scenes",
                     "scenes": [s.__dict__ for s in scenes]})
        await _set_job(job_id, progress=15)

        # ── 2 & 3. visuals + voice in parallel ───────────────────────
        aspect = style.get("aspect", "16:9")
        voice_id = style.get("voice_id")

        async def _visual(s: SceneSpec) -> tuple[int, str]:
            await _emit(job_id, "visual", "tool",
                        {"scene": s.idx, "status": "generating"})
            out = os.path.join(ctx.workdir, f"scene_{s.idx}.png")
            path = await image_provider().generate(s.visual_prompt, aspect, out)
            await _emit(job_id, "visual", "tool",
                        {"scene": s.idx, "status": "done"})
            return s.idx, path

        async def _voice(s: SceneSpec) -> tuple[int, str]:
            await _emit(job_id, "voice", "tool",
                        {"scene": s.idx, "status": "generating"})
            out = os.path.join(ctx.workdir, f"scene_{s.idx}.wav")
            path = await tts_provider().synthesize(s.narration, voice_id, out)
            await _emit(job_id, "voice", "tool",
                        {"scene": s.idx, "status": "done"})
            return s.idx, path

        visual_results = await asyncio.gather(*[_visual(sc) for sc in scenes])
        await _set_job(job_id, progress=55)
        voice_results = await asyncio.gather(*[_voice(sc) for sc in scenes])
        await _set_job(job_id, progress=75)

        visuals = dict(visual_results)
        voices = dict(voice_results)

        # ── 4. compose ───────────────────────────────────────────────
        await _emit(job_id, "compose", "agent", {"message": "Composing video..."})
        size = compositor.aspect_size(aspect)
        scene_clips: list[str] = []
        for sc in scenes:
            clip_path = os.path.join(ctx.workdir, f"clip_{sc.idx}.mp4")
            await compositor.render_scene(
                compositor.SceneClip(
                    image_path=visuals[sc.idx],
                    voice_path=voices[sc.idx],
                    duration_s=sc.duration_s,
                ),
                clip_path,
                size,
            )
            scene_clips.append(clip_path)

        final_path = os.path.join(ctx.workdir, "final.mp4")
        await compositor.concat_scenes(scene_clips, final_path)
        thumb_path = os.path.join(ctx.workdir, "thumb.jpg")
        await compositor.make_thumbnail(final_path, thumb_path)

        await _set_job(job_id, progress=90)

        # ── 5. upload + persist ──────────────────────────────────────
        final_url = await upload(final_path, s.renders_bucket,
                                 key_prefix=f"{owner_id}/{project_id}")
        thumb_url = await upload(thumb_path, s.renders_bucket,
                                 key_prefix=f"{owner_id}/{project_id}/thumbs")

        # Upload per-scene assets so the editor can swap them
        scene_visual_urls: dict[int, str] = {}
        scene_voice_urls: dict[int, str] = {}
        for sc in scenes:
            scene_visual_urls[sc.idx] = await upload(
                visuals[sc.idx], s.assets_bucket,
                key_prefix=f"{owner_id}/{project_id}/visuals",
            )
            scene_voice_urls[sc.idx] = await upload(
                voices[sc.idx], s.assets_bucket,
                key_prefix=f"{owner_id}/{project_id}/voices",
            )

        duration = sum(sc.duration_s for sc in scenes)

        with pg_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "update projects set status='ready', final_url=%s, thumbnail_url=%s, "
                "duration_s=%s where id=%s",
                (final_url, thumb_url, duration, str(project_id)),
            )
            for sc in scenes:
                cur.execute(
                    "update scenes set visual_url=%s, voice_url=%s "
                    "where project_id=%s and idx=%s",
                    (scene_visual_urls[sc.idx], scene_voice_urls[sc.idx],
                     str(project_id), sc.idx),
                )

        result = {
            "final_url": final_url,
            "thumbnail_url": thumb_url,
            "duration_s": duration,
            "scene_count": len(scenes),
        }
        await _emit(job_id, "done", "agent", result)
        await _set_job(job_id, status="done", progress=100, result=result)
        return result

    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        await _emit(job_id, "error", "system", {"error": err})
        await _set_job(job_id, status="failed", error=err)
        with pg_conn() as conn, conn.cursor() as cur:
            cur.execute("update projects set status='failed' where id=%s",
                        (str(project_id),))
        raise


async def _persist_scenes(project_id: UUID, scenes: list[SceneSpec]) -> None:
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("delete from scenes where project_id=%s", (str(project_id),))
        for s in scenes:
            cur.execute(
                "insert into scenes (project_id, idx, narration, visual_prompt, "
                "duration_s) values (%s, %s, %s, %s, %s)",
                (str(project_id), s.idx, s.narration, s.visual_prompt, s.duration_s),
            )
