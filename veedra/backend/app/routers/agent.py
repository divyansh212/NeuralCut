"""Agent runs: kick off a pipeline, stream live progress over SSE."""

from __future__ import annotations
import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.deps import get_current_user, CurrentUser
from app.models.schemas import AgentRunRequest, AgentRunResponse
from app.services.supabase import pg_conn
from app.agents import orchestrator
from app.workers.celery_app import run_agent_task

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse)
def run_agent(body: AgentRunRequest, user: CurrentUser = Depends(get_current_user)):
    """Create a project (if needed) and enqueue the agent pipeline."""
    with pg_conn() as conn, conn.cursor() as cur:
        if body.project_id:
            cur.execute(
                "select id from projects where id=%s and owner_id=%s",
                (str(body.project_id), str(user.id)),
            )
            if not cur.fetchone():
                raise HTTPException(404, "project not found")
            project_id = body.project_id
        else:
            cur.execute(
                "insert into projects (owner_id, title, prompt, style, status) "
                "values (%s, %s, %s, %s::jsonb, 'rendering') returning id",
                (str(user.id), body.prompt[:80] or "Untitled",
                 body.prompt, json.dumps(body.style)),
            )
            project_id = cur.fetchone()[0]

        cur.execute(
            "insert into jobs (owner_id, project_id, kind, status, payload) "
            "values (%s, %s, 'agent_run', 'queued', %s::jsonb) returning id",
            (str(user.id), str(project_id),
             json.dumps({"prompt": body.prompt, "style": body.style})),
        )
        job_id = cur.fetchone()[0]

    task = run_agent_task.delay(
        str(job_id), str(project_id), str(user.id), body.prompt, body.style
    )
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("update jobs set celery_id=%s where id=%s",
                    (task.id, str(job_id)))

    return AgentRunResponse(job_id=job_id, project_id=project_id)


@router.get("/stream/{job_id}")
async def stream_job(job_id: UUID, user: CurrentUser = Depends(get_current_user)):
    """SSE stream of agent_events for a job."""
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select id from jobs where id=%s and owner_id=%s",
            (str(job_id), str(user.id)),
        )
        if not cur.fetchone():
            raise HTTPException(404, "job not found")

    async def gen():
        # 1) replay existing events
        with pg_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "select step, role, content from agent_events "
                "where job_id=%s order by created_at",
                (str(job_id),),
            )
            for step, role, content in cur.fetchall():
                yield {"event": "agent", "data": json.dumps(
                    {"step": step, "role": role, "content": content})}

        # 2) live tail
        q = orchestrator.subscribe(job_id)
        try:
            while True:
                try:
                    evt = await asyncio.wait_for(q.get(), timeout=30)
                    yield {"event": "agent", "data": json.dumps(evt)}
                    if evt["step"] in ("done", "error"):
                        return
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            orchestrator.unsubscribe(job_id, q)

    return EventSourceResponse(gen())


@router.get("/jobs/{job_id}")
def get_job(job_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, owner_id, project_id, kind, status, progress, payload, "
            "result, error, created_at, updated_at "
            "from jobs where id=%s and owner_id=%s",
            (str(job_id), str(user.id)),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Not found")
        cols = [c.name for c in cur.description]
        return dict(zip(cols, row))
