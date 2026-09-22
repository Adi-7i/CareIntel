"""Secret-safe Celery configuration presence check."""

from careintel.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"redis_configured: {settings.redis_url is not None}")
    print(f"result_backend_configured: {settings.celery_result_backend is not None}")
