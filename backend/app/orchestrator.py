import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

from .compositor import compose
from .db import update_job, get_job_internal
from .events import publish_event, append_log
from .providers import get_providers
from .storage import upload_render


def emit(job_id, stage, status, detail=None):
    evt = {"stage": stage, "status": status, "detail": detail}
    append_log(job_id, evt)      # so late subscribers can replay
    publish_event(job_id, evt)   # live event via Redis pub/sub


def run_orchestrator(job_id: str):
    script, image, voice = get_providers()
    job = update_job(job_id, status="running")
    prompt = get_job_internal(job_id)["prompt"]
    work = tempfile.mkdtemp()
    try:
        # stage 1: script
        emit(job_id, "script", "start")
        scenes = script.generate(prompt)
        emit(job_id, "script", "done", {"scene_count": len(scenes)})

        # stage 2: visuals (parallel per scene)
        emit(job_id, "visuals", "start")
        with ThreadPoolExecutor() as ex:
            img_paths = list(ex.map(
                lambda s: image.generate(s["visual_desc"], os.path.join(work, f"img{s['scene']}.png")),
                scenes))
        emit(job_id, "visuals", "done")

        # stage 3: voice (parallel per scene)
        emit(job_id, "voice", "start")
        with ThreadPoolExecutor() as ex:
            wav_paths = list(ex.map(
                lambda s: voice.generate(s["narration"], os.path.join(work, f"v{s['scene']}.wav")),
                scenes))
        emit(job_id, "voice", "done")

        # stage 4: compose (ffmpeg — always real)
        emit(job_id, "compose", "start")
        out = compose(img_paths, wav_paths, os.path.join(work, "final.mp4"))
        url = upload_render(job_id, out)
        emit(job_id, "compose", "done", {"url": url})

        update_job(job_id, status="done", output_url=url)
        emit(job_id, "done", "done", {"url": url})
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))
        emit(job_id, "error", "failed", {"message": str(e)})
        raise
