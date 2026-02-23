"""
JeyaRamaDesk — Automation API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rules', views.AutomationRuleViewSet, basename='automation-rule')
router.register(r'logs', views.AutomationLogViewSet, basename='automation-log')

urlpatterns = [
    path('', include(router.urls)),
]
