"""
JeyaRamaDesk — SLA Models
Service Level Agreement policies with breach detection.
"""

from django.db import models
from django.conf import settings


class SLAPolicy(models.Model):
    """
    Defines response and resolution time expectations per priority level.
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'), ('medium', 'Medium'),
            ('high', 'High'), ('urgent', 'Urgent'),
        ],
        db_index=True,
    )
    response_time_hours = models.PositiveIntegerField(
        help_text='Maximum hours for first response',
    )
    resolution_time_hours = models.PositiveIntegerField(
        help_text='Maximum hours for resolution',
    )
    escalation_time_hours = models.PositiveIntegerField(
        default=0, help_text='Hours after which to auto-escalate (0 = disabled)',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jrd_sla_policies'
        verbose_name = 'SLA Policy'
        verbose_name_plural = 'SLA Policies'
        ordering = ['priority', 'name']
        indexes = [
            models.Index(fields=['priority', 'is_active'], name='idx_sla_prio_active'),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_priority_display()})'


class SLABreach(models.Model):
    """
    Records of SLA breaches for monitoring and reporting.
    """

    class BreachType(models.TextChoices):
        RESPONSE = 'response', 'Response Time Breached'
        RESOLUTION = 'resolution', 'Resolution Time Breached'

    id = models.BigAutoField(primary_key=True)
    ticket = models.ForeignKey(
        'tickets.Ticket', on_delete=models.CASCADE,
        related_name='sla_breaches', db_index=True,
    )
    policy = models.ForeignKey(
        SLAPolicy, on_delete=models.SET_NULL, null=True,
        related_name='breaches',
    )
    breach_type = models.CharField(max_length=10, choices=BreachType.choices)
    deadline = models.DateTimeField()
    breached_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        db_table = 'jrd_sla_breaches'
        ordering = ['-breached_at']
        indexes = [
            models.Index(fields=['ticket', 'breach_type'], name='idx_breach_ticket_type'),
            models.Index(fields=['breached_at'], name='idx_breach_time'),
        ]

    def __str__(self):
        return f'{self.get_breach_type_display()} — {self.ticket.ticket_id}'
