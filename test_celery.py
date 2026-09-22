from careintel.core.config import get_settings
settings = get_settings()
print("redis_url in config:", settings.redis_url)

# test celery_app.py logic
broker_url = (
    settings.redis_url.get_secret_value()
    if settings.redis_url
    else settings.celery_broker_url.get_secret_value()
)
print("broker_url computed:", broker_url)
