"""Celery worker that runs the agent pipeline asynchronously."""

from __future__ import annotations
import asyncio
from uuid import UUID

from celery import Celery

from app.config import get_settings
from app.agents.orchestrator import run_pipeline


_settings = get_settings()
celery_app = Celery(
    "veedra",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
)
celery_app.conf.task_track_started = True
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1


@celery_app.task(name="veedra.run_agent")
def run_agent_task(
    job_id: str, project_id: str, owner_id: str, prompt: str, style: dict
) -> dict:
    return asyncio.run(
        run_pipeline(UUID(job_id), UUID(project_id), UUID(owner_id), prompt, style)
    )
