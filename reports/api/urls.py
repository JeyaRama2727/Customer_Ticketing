"""
JeyaRamaDesk — Reports API URL Configuration
"""

from django.urls import path
from . import views

urlpatterns = [
    path('ticket-summary/', views.TicketSummaryAPI.as_view(), name='report-ticket-summary'),
]
