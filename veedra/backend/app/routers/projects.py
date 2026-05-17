"""Projects CRUD."""

from __future__ import annotations
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user, CurrentUser
from app.models.schemas import Project, ProjectCreate
from app.services.supabase import pg_conn

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects(user: CurrentUser = Depends(get_current_user)):
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, owner_id, title, prompt, style, status, thumbnail_url, "
            "final_url, duration_s, created_at, updated_at "
            "from projects where owner_id=%s order by created_at desc",
            (str(user.id),),
        )
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@router.post("", response_model=Project)
def create_project(
    body: ProjectCreate, user: CurrentUser = Depends(get_current_user)
):
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "insert into projects (owner_id, title, prompt, style) "
            "values (%s, %s, %s, %s::jsonb) "
            "returning id, owner_id, title, prompt, style, status, "
            "thumbnail_url, final_url, duration_s, created_at, updated_at",
            (str(user.id), body.title, body.prompt, json.dumps(body.style)),
        )
        cols = [c.name for c in cur.description]
        return dict(zip(cols, cur.fetchone()))


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, owner_id, title, prompt, style, status, thumbnail_url, "
            "final_url, duration_s, created_at, updated_at "
            "from projects where id=%s and owner_id=%s",
            (str(project_id), str(user.id)),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Not found")
        cols = [c.name for c in cur.description]
        return dict(zip(cols, row))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "delete from projects where id=%s and owner_id=%s",
            (str(project_id), str(user.id)),
        )


@router.get("/{project_id}/scenes")
def get_scenes(project_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with pg_conn() as conn, conn.cursor() as cur:
        # ownership check
        cur.execute(
            "select 1 from projects where id=%s and owner_id=%s",
            (str(project_id), str(user.id)),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Not found")
        cur.execute(
            "select id, project_id, idx, narration, visual_prompt, visual_url, "
            "voice_url, duration_s from scenes where project_id=%s order by idx",
            (str(project_id),),
        )
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
