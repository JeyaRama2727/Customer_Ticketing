"""
JeyaRamaDesk — SLA Service Layer
"""

import logging
from django.utils import timezone
from django.db import transaction
from sla.models import SLAPolicy, SLABreach
from tickets.models import Ticket

logger = logging.getLogger('jeyaramadesk')


class SLAService:
    """Business logic for SLA management."""

    @staticmethod
    def check_all_breaches():
        """
        Check all open tickets for SLA breaches.
        Called periodically by Celery beat.
        """
        now = timezone.now()
        breaches_found = 0

        # Response time breaches
        response_breached = Ticket.objects.filter(
            sla_response_deadline__lt=now,
            first_response_at__isnull=True,
            status__in=['open', 'in_progress', 'pending'],
        ).exclude(
            sla_breaches__breach_type='response',
        )

        for ticket in response_breached:
            SLABreach.objects.create(
                ticket=ticket,
                policy=ticket.sla_policy,
                breach_type=SLABreach.BreachType.RESPONSE,
                deadline=ticket.sla_response_deadline,
            )
            ticket.sla_response_met = False
            ticket.save(update_fields=['sla_response_met'])
            breaches_found += 1
            # Send notification
            try:
                from notifications.services.notification_service import NotificationService
                NotificationService.notify_sla_breach(ticket, breach_type='response')
            except Exception as e:
                logger.error(f'SLA breach notification error: {e}')

        # Resolution time breaches
        resolution_breached = Ticket.objects.filter(
            sla_resolution_deadline__lt=now,
            status__in=['open', 'in_progress', 'pending'],
        ).exclude(
            sla_breaches__breach_type='resolution',
        )

        for ticket in resolution_breached:
            SLABreach.objects.create(
                ticket=ticket,
                policy=ticket.sla_policy,
                breach_type=SLABreach.BreachType.RESOLUTION,
                deadline=ticket.sla_resolution_deadline,
            )
            ticket.sla_resolution_met = False
            ticket.save(update_fields=['sla_resolution_met'])
            breaches_found += 1
            # Send notification
            try:
                from notifications.services.notification_service import NotificationService
                NotificationService.notify_sla_breach(ticket, breach_type='resolution')
            except Exception as e:
                logger.error(f'SLA breach notification error: {e}')

        if breaches_found:
            logger.warning(f'SLA Check: {breaches_found} new breaches detected.')

        return breaches_found

    @staticmethod
    def get_sla_stats():
        """Get SLA performance statistics."""
        from django.db.models import Count, Q, F

        total_with_sla = Ticket.objects.filter(sla_policy__isnull=False).count()
        if total_with_sla == 0:
            return {
                'total': 0,
                'response_met': 0, 'response_breached': 0, 'response_rate': 0,
                'resolution_met': 0, 'resolution_breached': 0, 'resolution_rate': 0,
            }

        stats = Ticket.objects.filter(sla_policy__isnull=False).aggregate(
            response_met=Count('id', filter=Q(sla_response_met=True)),
            response_breached=Count('id', filter=Q(sla_response_met=False)),
            resolution_met=Count('id', filter=Q(sla_resolution_met=True)),
            resolution_breached=Count('id', filter=Q(sla_resolution_met=False)),
        )

        response_total = stats['response_met'] + stats['response_breached']
        resolution_total = stats['resolution_met'] + stats['resolution_breached']

        stats['total'] = total_with_sla
        stats['total_breaches'] = SLABreach.objects.count()
        stats['response_rate'] = round(
            (stats['response_met'] / response_total * 100) if response_total else 0, 1
        )
        stats['resolution_rate'] = round(
            (stats['resolution_met'] / resolution_total * 100) if resolution_total else 0, 1
        )
        stats['response_met_rate'] = stats['response_rate']
        stats['resolution_met_rate'] = stats['resolution_rate']

        return stats
