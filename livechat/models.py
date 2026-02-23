"""
JeyaRamaDesk — Live Chat Models
Real-time messaging between customers and support agents.
"""

import uuid
from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    """
    A chat room / conversation thread.
    Each room is tied to a customer and optionally an agent and ticket.
    """

    class Status(models.TextChoices):
        WAITING   = 'waiting',   'Waiting for Agent'
        ACTIVE    = 'active',    'Active'
        CLOSED    = 'closed',    'Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_customer',
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_rooms_as_agent',
    )
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_rooms',
        help_text='Linked support ticket (optional).',
    )
    subject = models.CharField(max_length=255, default='Live Chat')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['customer', 'status'], name='idx_chat_cust_status'),
            models.Index(fields=['agent', 'status'], name='idx_chat_agent_status'),
            models.Index(fields=['-updated_at'], name='idx_chat_updated'),
        ]

    def __str__(self):
        return f'Chat {str(self.id)[:8]} — {self.subject}'


class ChatMessage(models.Model):
    """
    A single message within a chat room.
    """

    class MessageType(models.TextChoices):
        TEXT   = 'text',   'Text'
        SYSTEM = 'system', 'System'
        IMAGE  = 'image',  'Image'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_messages',
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at'], name='idx_chatmsg_room_time'),
            models.Index(fields=['room', 'is_read'], name='idx_chatmsg_unread'),
        ]

    def __str__(self):
        sender_name = (self.sender.full_name or self.sender.email) if self.sender else 'System'
        return f'{sender_name}: {self.content[:50]}'
