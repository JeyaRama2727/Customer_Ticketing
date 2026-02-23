"""
JeyaRamaDesk — SLA Celery Tasks
"""

from celery import shared_task
import logging

logger = logging.getLogger('jeyaramadesk')


@shared_task(name='sla.tasks.check_sla_breaches')
def check_sla_breaches():
    """Periodic task to detect SLA breaches."""
    from sla.services.sla_service import SLAService
    count = SLAService.check_all_breaches()
    logger.info(f'SLA breach check completed. {count} new breaches.')
    return count
