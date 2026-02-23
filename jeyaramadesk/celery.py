"""
JeyaRamaDesk — Celery Application
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jeyaramadesk.settings')

app = Celery('jeyaramadesk')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug/health-check task."""
    print(f'Request: {self.request!r}')
