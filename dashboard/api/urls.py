"""
JeyaRamaDesk — Dashboard API URL Configuration
"""

from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.DashboardStatsAPI.as_view(), name='dashboard-stats'),
]
