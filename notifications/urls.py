"""JeyaRamaDesk — Notification URL Configuration"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<uuid:pk>/open/', views.notification_open, name='open'),
    path('<uuid:pk>/read/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('unread-count/', views.unread_count_api, name='unread_count'),
]
