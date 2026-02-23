"""
JeyaRamaDesk — Enterprise Customer Support Platform
"""

# Ensure Celery app is loaded when Django starts
from .celery import app as celery_app  # noqa

__all__ = ('celery_app',)
