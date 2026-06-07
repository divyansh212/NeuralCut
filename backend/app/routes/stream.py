"""SSE endpoint. Replays the joblog buffer, then subscribes to the Redis channel
for live events. EventSource cannot send headers, so the short-lived Supabase
access token is passed as a query param and verified server-side; ownership of
the job is then confirmed before any events are streamed.
"""

import asyncio
import json

import jwt
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..config import settings
from ..db import get_job

router = APIRouter()


def _verify_token(token: str) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(500, "Server auth not configured")
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    if not payload.get("sub"):
        raise HTTPException(401, "Token missing subject")
    return {"id": payload["sub"]}


async def event_source(job_id: str):
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    # 1) replay anything that already happened
    backlog = await r.lrange(f"joblog:{job_id}", 0, -1)
    for item in backlog:
        yield f"data: {item}\n\n"
    # 2) subscribe for live events
    pubsub = r.pubsub()
    await pubsub.subscribe(f"job:{job_id}")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15)
            if message is None:
                yield ": ping\n\n"          # heartbeat so proxies don't drop idle conn
                continue
            data = message["data"]
            yield f"data: {data}\n\n"
            evt = json.loads(data)
            if evt.get("stage") == "done" or evt.get("status") == "failed":
                break
    finally:
        await pubsub.unsubscribe(f"job:{job_id}")
        await pubsub.aclose()
        await r.aclose()


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str, token: str = Query(...)):
    user = _verify_token(token)
    # authorize: confirm the job belongs to this user before streaming
    job = get_job(job_id, user_id=user["id"])
    if not job:
        raise HTTPException(404, "Job not found")
    return StreamingResponse(
        event_source(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
