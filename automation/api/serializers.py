"""
JeyaRamaDesk — Automation API Serializers
"""

from rest_framework import serializers
from automation.models import AutomationRule, AutomationLog


class AutomationRuleSerializer(serializers.ModelSerializer):
    """Serializer for automation rules."""
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True, default=''
    )

    class Meta:
        model = AutomationRule
        fields = [
            'id', 'name', 'description', 'trigger_event',
            'conditions', 'action_type', 'action_params',
            'priority_order', 'is_active', 'stop_processing',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AutomationLogSerializer(serializers.ModelSerializer):
    """Serializer for automation execution logs."""
    rule_name = serializers.CharField(source='rule.name', read_only=True, default='')
    ticket_id = serializers.CharField(source='ticket.ticket_id', read_only=True)

    class Meta:
        model = AutomationLog
        fields = [
            'id', 'rule', 'rule_name', 'ticket', 'ticket_id',
            'status', 'action_taken', 'error_message', 'executed_at',
        ]
        read_only_fields = ['id', 'executed_at']
