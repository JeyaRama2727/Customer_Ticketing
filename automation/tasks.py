"""
JeyaRamaDesk — Automation Celery Tasks
Background tasks for running automation rules on idle tickets.
"""

from celery import shared_task
import logging

logger = logging.getLogger('jeyaramadesk')


@shared_task(name='automation.run_idle_ticket_rules')
def run_idle_ticket_rules():
    """
    Periodic task: Find tickets that have been idle (no updates)
    and run 'ticket_idle' automation rules against them.
    Runs every minute via Celery Beat.
    """
    from django.utils import timezone
    from datetime import timedelta
    from tickets.models import Ticket
    from automation.services.automation_service import AutomationService
    from automation.models import AutomationRule

    # Only process if there are active idle rules
    idle_rules = AutomationRule.objects.filter(
        trigger_event='ticket_idle',
        is_active=True,
    )
    if not idle_rules.exists():
        return 'No active idle rules'

    # Find tickets idle for more than 24 hours
    idle_threshold = timezone.now() - timedelta(hours=24)
    idle_tickets = Ticket.objects.filter(
        status__in=['open', 'assigned', 'in_progress'],
        updated_at__lt=idle_threshold,
    ).select_related('assigned_agent', 'customer', 'category')

    count = 0
    for ticket in idle_tickets[:100]:  # Process max 100 per run
        AutomationService.run_rules('ticket_idle', ticket)
        count += 1

    logger.info(f'Automation: Processed {count} idle tickets')
    return f'Processed {count} idle tickets'
