"""JeyaRamaDesk — Live Chat WebSocket Routing"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'desk/ws/chat/(?P<room_id>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
]
