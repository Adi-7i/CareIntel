import os
from unittest import mock

from careintel.core.config import Settings


@mock.patch.dict(
    os.environ,
    {
        "APP_ENV": "development",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "SECRET_KEY": "test",
        "REDIS_URL": "redis://test-redis:6379/2",
    },
)
def test_celery_broker_prefers_redis_url():
    """Verify that if REDIS_URL is provided, it is used as the broker."""
    # We must instantiate Settings directly to capture the mocked environ,
    # since get_settings() is cached.
    settings = Settings(_env_file=None)

    # Simulate what celery_app.py does
    broker_url = (
        settings.redis_url.get_secret_value()
        if settings.redis_url
        else settings.celery_broker_url.get_secret_value()
    )

    assert broker_url == "redis://test-redis:6379/2"


@mock.patch.dict(
    os.environ,
    {
        "APP_ENV": "development",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "SECRET_KEY": "test",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "REDIS_URL": "",
    },
)
def test_celery_broker_falls_back_to_celery_broker_url():
    """Verify that if REDIS_URL is missing, it falls back to CELERY_BROKER_URL."""
    # Ensure REDIS_URL is explicitly clear
    if "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]

    settings = Settings(_env_file=None)

    broker_url = (
        settings.redis_url.get_secret_value()
        if settings.redis_url
        else settings.celery_broker_url.get_secret_value()
    )

    assert broker_url == "redis://localhost:6379/1"


def test_celery_app_configuration():
    """Verify Celery task configurations."""
    # Import inside test to avoid loading cached settings at module level
    from careintel.workers.celery_app import celery_app

    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    # Default queue should be matched
    assert celery_app.conf.task_default_queue == "careintel_default"
