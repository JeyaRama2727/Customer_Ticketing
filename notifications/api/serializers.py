"""JeyaRamaDesk — Notification API Serializers"""

from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Read-only serializer for Notification instances."""

    ticket_id_display = serializers.CharField(
        source='ticket.ticket_id', read_only=True, default=None,
    )

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'ticket', 'ticket_id_display',
            'is_read', 'read_at', 'created_at',
        ]
        read_only_fields = fields
