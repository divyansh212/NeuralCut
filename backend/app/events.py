"""Live progress events travel through Redis pub/sub — NEVER an in-memory dict.

The Celery worker and the FastAPI web server are separate processes (separate
memory, often separate containers). A module-level dict would have the worker
write to its copy and the SSE endpoint read from a different empty copy — events
vanish silently. Redis bridges the process boundary: the worker PUBLISHes; the
SSE endpoint SUBSCRIBEs. A short replay log lets a client connecting mid-job see
the events it missed.
"""

import json

import redis as sync_redis

from .config import settings

# Worker side is synchronous (Celery tasks run sync) -> sync client here.
_sync = sync_redis.from_url(settings.REDIS_URL, decode_responses=True)


def channel(job_id: str) -> str:
    return f"job:{job_id}"


def publish_event(job_id: str, event: dict) -> None:
    """Called from inside the Celery worker after each agent step."""
    _sync.publish(channel(job_id), json.dumps(event))


def append_log(job_id: str, event: dict, ttl: int = 3600) -> None:
    """Replay buffer so a late subscriber sees history. Expires after `ttl`s."""
    key = f"joblog:{job_id}"
    _sync.rpush(key, json.dumps(event))
    _sync.expire(key, ttl)
