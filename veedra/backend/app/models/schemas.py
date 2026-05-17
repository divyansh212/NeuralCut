"""Pydantic schemas for API I/O."""
from __future__ import annotations
from typing import Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Projects ────────────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    title: str = "Untitled"
    prompt: Optional[str] = None
    style: dict = Field(default_factory=dict)


class Project(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    prompt: Optional[str]
    style: dict
    status: str
    thumbnail_url: Optional[str]
    final_url: Optional[str]
    duration_s: Optional[float]
    created_at: datetime
    updated_at: datetime


# ─── Scenes ──────────────────────────────────────────────────────────
class Scene(BaseModel):
    id: Optional[UUID] = None
    project_id: UUID
    idx: int
    narration: str
    visual_prompt: str
    visual_url: Optional[str] = None
    voice_url: Optional[str] = None
    duration_s: float = 4.0


# ─── Agent run ───────────────────────────────────────────────────────
class AgentRunRequest(BaseModel):
    project_id: Optional[UUID] = None
    prompt: str
    style: dict = Field(default_factory=dict)
    """style keys: aspect ('9:16'|'16:9'|'1:1'), tone, voice_id, scenes (int hint)"""


class AgentRunResponse(BaseModel):
    job_id: UUID
    project_id: UUID


# ─── Jobs ────────────────────────────────────────────────────────────
class Job(BaseModel):
    id: UUID
    owner_id: UUID
    project_id: Optional[UUID]
    kind: str
    status: Literal["queued", "running", "done", "failed"]
    progress: int
    payload: dict
    result: Optional[dict]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime


# ─── Agent event (SSE payload) ───────────────────────────────────────
class AgentEvent(BaseModel):
    step: str             # script | visual | voice | compose | done
    role: str             # agent | tool | system
    content: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
