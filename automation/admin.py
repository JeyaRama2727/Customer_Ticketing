"""
JeyaRamaDesk — Automation Admin
Admin configuration for automation rules and logs.
"""

from django.contrib import admin
from .models import AutomationRule, AutomationLog


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    """Admin for automation rules."""

    list_display = [
        'name', 'trigger_event', 'action_type',
        'priority_order', 'is_active', 'created_at',
    ]
    list_filter = ['trigger_event', 'action_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'priority_order']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['priority_order', '-created_at']

    fieldsets = (
        ('Rule Details', {
            'fields': ('id', 'name', 'description'),
        }),
        ('Trigger & Conditions', {
            'fields': ('trigger_event', 'conditions'),
        }),
        ('Action', {
            'fields': ('action_type', 'action_params'),
        }),
        ('Execution', {
            'fields': ('priority_order', 'is_active', 'stop_processing'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )


@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    """Admin for automation execution logs."""

    list_display = ['rule', 'ticket', 'status', 'executed_at']
    list_filter = ['status', 'executed_at']
    search_fields = ['rule__name', 'action_taken']
    readonly_fields = [
        'id', 'rule', 'ticket', 'status',
        'action_taken', 'error_message', 'executed_at',
    ]
    ordering = ['-executed_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
