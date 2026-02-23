"""
JeyaRamaDesk — Live Chat WebSocket Consumer
Handles real-time bidirectional messaging between customer and agent.
"""

import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('jeyaramadesk')


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for a specific chat room.
    Both the customer and agent connect to the same room group.
    """

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        # Note: We don't broadcast join events here because page refreshes
        # would spam "X joined" messages. Meaningful join events (agent
        # picking up a waiting room) are handled in views.py instead.
        logger.debug(f'WS Chat connected: {self.user.email} → room {self.room_id}')

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Don't broadcast leave events — page navigation / refresh shouldn't
            # spam "X left" messages. Only close_chat matters for ending a session.
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from the WebSocket client."""
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        message_type = data.get('type', 'text')
        content = data.get('message', '').strip()
        if not content:
            return

        # Persist the message to the database
        msg = await self._save_message(content, message_type)

        # Broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(msg['id']),
                    'content': msg['content'],
                    'message_type': msg['message_type'],
                    'sender_id': str(self.user.id),
                    'sender_name': await self._get_display_name(),
                    'sender_role': await self._get_role(),
                    'created_at': msg['created_at'],
                },
            },
        )

    # ── Group event handlers ──────────────────────────────────

    async def chat_message(self, event):
        """Send a chat message event to the WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
        }))

    async def user_event(self, event):
        """Send user join/leave event to the WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'user_event',
            'event': event['event'],
            'user_name': event['user_name'],
            'user_id': event['user_id'],
        }))

    async def typing_event(self, event):
        """Send typing indicator to the WebSocket client."""
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))

    # ── Database helpers (sync → async) ───────────────────────

    @database_sync_to_async
    def _save_message(self, content, message_type='text'):
        from livechat.models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(pk=self.room_id)
        msg = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=content,
            message_type=message_type,
        )
        # Update room timestamp
        room.save(update_fields=['updated_at'])
        return {
            'id': msg.id,
            'content': msg.content,
            'message_type': msg.message_type,
            'created_at': msg.created_at.isoformat(),
        }

    @database_sync_to_async
    def _get_display_name(self):
        name = self.user.full_name
        return name if name else self.user.email

    @database_sync_to_async
    def _get_role(self):
        return self.user.role
