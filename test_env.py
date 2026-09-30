"""Secret-safe local configuration presence check."""

from careintel.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"redis_configured: {settings.redis_url is not None}")
    print(f"celery_fallback_configured: {settings.celery_broker_url is not None}")
