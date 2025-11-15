import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "high_traffic.settings")

app = Celery("high_traffic")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def ping(self):
    """Simple heartbeat task used by health checks."""
    return "pong"
