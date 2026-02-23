"""
JeyaRamaDesk — WebSocket Consumer for Real-time Notifications
Delivers notifications to authenticated users via a per-user channel group.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('jeyaramadesk')


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that adds the connecting user to a personal
    notification group so they can receive real-time pushes.
    """

    async def connect(self):
        """Accept the connection and join the user's notification group."""
        self.user = self.scope.get('user')
        if self.user and self.user.is_authenticated:
            self.group_name = f'notifications_{self.user.id}'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            logger.debug(f'WS connected: {self.user.email}')
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Leave the notification group on disconnect."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.debug(f'WS disconnected: {self.user.email}')

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages (currently unused — one-way push)."""
        pass

    async def send_notification(self, event):
        """
        Handler for the ``send_notification`` event type dispatched
        by NotificationService._push_realtime().
        """
        await self.send(text_data=json.dumps(event['notification']))
