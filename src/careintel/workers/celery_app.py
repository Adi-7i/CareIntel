"""
Celery Application Factory.
"""

from celery import Celery

from careintel.core.config import get_settings


def create_celery_app() -> Celery:
    """
    Configure and return the Celery application instance.
    """
    settings = get_settings()

    # Use redis_url if provided (production standard), fallback to celery_broker_url (dev)
    broker_url = (
        settings.redis_url.get_secret_value()
        if settings.redis_url
        else settings.celery_broker_url.get_secret_value()
    )

    backend_url = (
        settings.redis_url.get_secret_value()
        if settings.redis_url
        else (
            settings.celery_result_backend.get_secret_value()
            if settings.celery_result_backend
            else None
        )
    )

    app = Celery(
        "careintel",
        broker=broker_url,
        backend=backend_url,
    )

    app.conf.update(
        task_default_queue=settings.celery_task_default_queue,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
        task_soft_time_limit=settings.celery_task_soft_time_limit,
        task_time_limit=settings.celery_task_hard_time_limit,
        # Include task modules here (these will be created in next steps)
        imports=[
            "careintel.application.workflow.outbox_dispatcher",
            "careintel.workers.processing_tasks",
            "careintel.workers.ai_tasks",
            "careintel.workers.retrieval_tasks",
            "careintel.workers.workflow_tasks",
        ],
    )

    return app


celery_app = create_celery_app()
