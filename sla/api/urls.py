"""
JeyaRamaDesk — SLA API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'policies', views.SLAPolicyViewSet, basename='sla-policy')
router.register(r'breaches', views.SLABreachViewSet, basename='sla-breach')

urlpatterns = [
    path('', include(router.urls)),
]
