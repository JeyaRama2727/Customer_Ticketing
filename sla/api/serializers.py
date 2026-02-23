"""
JeyaRamaDesk — SLA API Serializers
REST Framework serializers for SLA policies and breaches.
"""

from rest_framework import serializers
from sla.models import SLAPolicy, SLABreach


class SLAPolicySerializer(serializers.ModelSerializer):
    """Serializer for SLA policies."""

    class Meta:
        model = SLAPolicy
        fields = [
            'id', 'name', 'priority', 'response_time_hours',
            'resolution_time_hours', 'escalation_time_hours',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SLABreachSerializer(serializers.ModelSerializer):
    """Serializer for SLA breach records."""

    ticket_id = serializers.CharField(source='ticket.ticket_id', read_only=True)
    ticket_title = serializers.CharField(source='ticket.title', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)

    class Meta:
        model = SLABreach
        fields = [
            'id', 'ticket', 'ticket_id', 'ticket_title',
            'policy', 'policy_name', 'breach_type',
            'deadline', 'breached_at', 'notified',
        ]
        read_only_fields = ['id', 'breached_at']
