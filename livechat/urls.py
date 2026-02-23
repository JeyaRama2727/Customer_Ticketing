"""JeyaRamaDesk — Live Chat URL Configuration"""

from django.urls import path
from . import views

app_name = 'livechat'

urlpatterns = [
    path('', views.chat_room_list, name='room_list'),
    path('start/', views.start_chat, name='start_chat'),
    path('<uuid:room_id>/', views.chat_room, name='room'),
    path('<uuid:room_id>/close/', views.close_chat, name='close_chat'),
    path('<uuid:room_id>/send/', views.send_message, name='send_message'),
    path('<uuid:room_id>/messages/', views.fetch_messages, name='fetch_messages'),
    path('unread-count/', views.unread_chat_count, name='unread_count'),
]
