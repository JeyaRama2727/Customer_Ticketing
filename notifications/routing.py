"""JeyaRamaDesk — WebSocket Routing for Notifications"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'desk/ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
