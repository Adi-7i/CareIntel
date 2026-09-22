from dotenv import load_dotenv
load_dotenv()
from careintel.core.config import get_settings
settings = get_settings()
print("REDIS_URL:", settings.redis_url)
print("CELERY_BROKER:", settings.celery_broker_url)

from careintel.workers.celery_app import celery_app
print("APP BROKER:", celery_app.conf.broker_url)
