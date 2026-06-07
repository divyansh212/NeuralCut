from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import jobs, stream

app = FastAPI(title="NeuralCut API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(stream.router)


@app.get("/health")
def health():
    return {"ok": True, "service": "neuralcut", "mode": settings.PROVIDER_MODE}
