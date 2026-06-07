from celery import Celery

from .config import settings
from .orchestrator import run_orchestrator

celery_app = Celery("neuralcut", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(task_track_started=True, broker_connection_retry_on_startup=True)


@celery_app.task(name="run_pipeline")
def run_pipeline(job_id: str):
    # Emits events via Redis pub/sub (see orchestrator.py + events.py)
    run_orchestrator(job_id)
