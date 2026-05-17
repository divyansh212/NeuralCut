"""Veedra backend entry point."""

from __future__ import annotations
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import projects, agent, understand


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="Veedra API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Local-storage fallback: serve renders/assets directly when Supabase
    # Storage isn't configured.
    static_root = Path(s.local_storage_dir)
    static_root.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/health")
    def health():
        return {"ok": True, "mode": s.provider_mode}

    app.include_router(projects.router)
    app.include_router(agent.router)
    app.include_router(understand.router)
    return app


app = create_app()
