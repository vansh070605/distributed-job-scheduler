from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "scheduler_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Auto-discover task modules
    imports=[
        "app.workers.tasks",
        "app.scheduler.tasks",
    ],
    beat_schedule={
        "poll-due-jobs-every-5s": {
            "task": "app.scheduler.tasks.poll_and_enqueue_due_jobs",
            "schedule": 5.0,
        },
        "reap-stale-workers-every-10s": {
            "task": "app.scheduler.tasks.reap_stale_workers",
            "schedule": 10.0,
        },
        "aggregate-metrics-every-10s": {
            "task": "app.scheduler.tasks.aggregate_queue_metrics",
            "schedule": 10.0,
        },
    },
)
