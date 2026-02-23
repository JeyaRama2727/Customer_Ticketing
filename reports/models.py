"""\nJeyaRamaDesk — Reports Models\nSaved report configurations for recurring analytics.\n"""

from django.db import models
from django.conf import settings
import uuid


class SavedReport(models.Model):
    """Saved report configuration for quick access."""

    class ReportType(models.TextChoices):
        TICKET_SUMMARY = 'ticket_summary', 'Ticket Summary'
        AGENT_PERFORMANCE = 'agent_performance', 'Agent Performance'
        SLA_COMPLIANCE = 'sla_compliance', 'SLA Compliance'
        CATEGORY_BREAKDOWN = 'category_breakdown', 'Category Breakdown'
        CUSTOMER_SATISFACTION = 'customer_satisfaction', 'Customer Satisfaction'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Report Name', max_length=200)
    report_type = models.CharField(
        'Type', max_length=30,
        choices=ReportType.choices,
    )
    filters = models.JSONField(
        'Filters', default=dict, blank=True,
        help_text='Saved filter parameters (date range, agent, etc.)',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_reports',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jrd_saved_reports'
        verbose_name = 'Saved Report'
        verbose_name_plural = 'Saved Reports'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} ({self.get_report_type_display()})'
