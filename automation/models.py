"""
JeyaRamaDesk — Automation Models
Rule-based automation engine for ticket workflows.
Supports trigger conditions, actions, and scheduling.
Designed for millions of records with proper indexing.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class AutomationRule(models.Model):
    """
    Defines an automation rule with trigger conditions and actions.
    Rules are evaluated against tickets to perform automatic actions
    like assignment, priority changes, tagging, and notifications.
    """

    class TriggerEvent(models.TextChoices):
        TICKET_CREATED = 'ticket_created', 'Ticket Created'
        TICKET_UPDATED = 'ticket_updated', 'Ticket Updated'
        TICKET_ASSIGNED = 'ticket_assigned', 'Ticket Assigned'
        TICKET_COMMENTED = 'ticket_commented', 'Comment Added'
        SLA_BREACH = 'sla_breach', 'SLA Breach'
        TICKET_IDLE = 'ticket_idle', 'Ticket Idle'

    class ActionType(models.TextChoices):
        ASSIGN_AGENT = 'assign_agent', 'Assign to Agent'
        CHANGE_PRIORITY = 'change_priority', 'Change Priority'
        CHANGE_STATUS = 'change_status', 'Change Status'
        ADD_TAG = 'add_tag', 'Add Tag'
        SEND_NOTIFICATION = 'send_notification', 'Send Notification'
        ESCALATE = 'escalate', 'Escalate Ticket'
        ADD_COMMENT = 'add_comment', 'Add Internal Note'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Rule Name', max_length=200)
    description = models.TextField('Description', blank=True, default='')

    # ── Trigger ───────────────────────────────────────────
    trigger_event = models.CharField(
        'Trigger Event',
        max_length=30,
        choices=TriggerEvent.choices,
        db_index=True,
    )

    # ── Conditions (JSON) ─────────────────────────────────
    # Example: {"priority": "urgent", "category": "billing"}
    conditions = models.JSONField(
        'Conditions',
        default=dict,
        blank=True,
        help_text='JSON conditions to match against ticket fields.',
    )

    # ── Action ────────────────────────────────────────────
    action_type = models.CharField(
        'Action Type',
        max_length=30,
        choices=ActionType.choices,
    )

    # JSON action parameters
    # Example for assign_agent: {"agent_id": "uuid-here"}
    # Example for change_priority: {"priority": "high"}
    # Example for send_notification: {"message": "...", "recipients": "agent"}
    action_params = models.JSONField(
        'Action Parameters',
        default=dict,
        blank=True,
        help_text='JSON parameters for the action to execute.',
    )

    # ── Ordering & Status ─────────────────────────────────
    priority_order = models.PositiveIntegerField(
        'Execution Order',
        default=0,
        help_text='Lower numbers execute first.',
    )
    is_active = models.BooleanField('Active', default=True, db_index=True)
    stop_processing = models.BooleanField(
        'Stop Processing',
        default=False,
        help_text='If True, stop evaluating further rules after this one matches.',
    )

    # ── Metadata ──────────────────────────────────────────
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rules',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jrd_automation_rules'
        verbose_name = 'Automation Rule'
        verbose_name_plural = 'Automation Rules'
        ordering = ['priority_order', '-created_at']
        indexes = [
            models.Index(
                fields=['trigger_event', 'is_active'],
                name='idx_rule_trigger_active',
            ),
            models.Index(
                fields=['priority_order'],
                name='idx_rule_priority',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_trigger_event_display()})'


class AutomationLog(models.Model):
    """
    Tracks every automation rule execution for auditing and debugging.
    """

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Skipped'

    id = models.BigAutoField(primary_key=True)
    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs',
    )
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='automation_logs',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS,
    )
    action_taken = models.TextField('Action Taken', blank=True, default='')
    error_message = models.TextField('Error', blank=True, default='')
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jrd_automation_logs'
        verbose_name = 'Automation Log'
        verbose_name_plural = 'Automation Logs'
        ordering = ['-executed_at']
        indexes = [
            models.Index(
                fields=['rule', 'executed_at'],
                name='idx_autolog_rule_date',
            ),
            models.Index(
                fields=['ticket', 'executed_at'],
                name='idx_autolog_ticket_date',
            ),
        ]

    def __str__(self):
        return f'Rule "{self.rule}" on Ticket {self.ticket_id} — {self.status}'
