from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.ping")
def ping() -> str:
    """Trivial task used in Sprint 1 to verify Celery + Redis wiring end-to-end."""
    return "pong"
