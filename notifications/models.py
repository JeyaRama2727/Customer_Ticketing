"""JeyaRamaDesk — Notification Models"""

import uuid
from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    In-app notification delivered to a user.
    Supports linking to the originating ticket and categorisation
    by type so the UI can render appropriate icons / colours.
    """

    class NotificationType(models.TextChoices):
        TICKET_CREATED    = 'ticket_created',   'Ticket Created'
        TICKET_ASSIGNED   = 'ticket_assigned',  'Ticket Assigned'
        TICKET_UPDATED    = 'ticket_updated',   'Ticket Updated'
        TICKET_RESOLVED   = 'ticket_resolved',  'Ticket Resolved'
        COMMENT_ADDED     = 'comment_added',    'Comment Added'
        STATUS_CHANGE     = 'status_change',    'Status Changed'
        PRIORITY_CHANGE   = 'priority_change',  'Priority Changed'
        SLA_BREACH        = 'sla_breach',       'SLA Breach'
        AUTOMATION        = 'automation',       'Automation'
        SYSTEM            = 'system',           'System'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='Recipient of this notification.',
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, default='')
    notification_type = models.CharField(
        max_length=25,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True,
    )
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Ticket this notification relates to (optional).',
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_notif_user_created'),
            models.Index(fields=['user', 'is_read'], name='idx_notif_user_unread'),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'{self.title} → {self.user.full_name or self.user.email}'

    def mark_read(self):
        """Mark this notification as read."""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
