"""
JeyaRamaDesk — Ticket URL Configuration
"""

from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.ticket_list_view, name='list'),
    path('create/', views.ticket_create_view, name='create'),
    path('<str:ticket_id>/', views.ticket_detail_view, name='detail'),
    path('<str:ticket_id>/update/', views.ticket_update_view, name='update'),
    path('<str:ticket_id>/comment/', views.ticket_comment_view, name='comment'),
    path('<str:ticket_id>/assign/', views.ticket_assign_view, name='assign'),
]
