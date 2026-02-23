"""
JeyaRamaDesk — Ticket Signals
Automated actions triggered by ticket events.
Sends real-time notifications for ticket creation, comments,
assignment changes, status changes, and priority changes.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from tickets.models import Ticket, TicketComment
import logging

logger = logging.getLogger('jeyaramadesk')


# ── Cache old values before save so we can detect changes ────

@receiver(pre_save, sender=Ticket)
def ticket_pre_save(sender, instance, **kwargs):
    """Stash previous field values so post_save can detect changes."""
    if instance.pk:
        try:
            old = Ticket.objects.get(pk=instance.pk)
            instance._old_assigned_agent_id = old.assigned_agent_id
            instance._old_status = old.status
            instance._old_priority = old.priority
        except Ticket.DoesNotExist:
            instance._old_assigned_agent_id = None
            instance._old_status = None
            instance._old_priority = None


@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    """Handle post-save events for tickets."""
    try:
        from notifications.services.notification_service import NotificationService
    except Exception as e:
        logger.error(f'Could not import NotificationService: {e}')
        return

    if created:
        # ── New ticket → notify managers / superadmins ────────
        try:
            NotificationService.notify_new_ticket(instance)
        except Exception as e:
            logger.error(f'Notification error on ticket create: {e}')
        return

    # ── Assignment changed ────────────────────────────────────
    old_agent_id = getattr(instance, '_old_assigned_agent_id', None)
    if instance.assigned_agent_id and instance.assigned_agent_id != old_agent_id:
        try:
            NotificationService.notify_ticket_assigned(instance)
        except Exception as e:
            logger.error(f'Notification error on ticket assign: {e}')

    # ── Status changed ────────────────────────────────────────
    old_status = getattr(instance, '_old_status', None)
    if old_status and instance.status != old_status:
        try:
            NotificationService.notify_status_change(instance, old_status)
        except Exception as e:
            logger.error(f'Notification error on status change: {e}')

    # ── Priority changed ─────────────────────────────────────
    old_priority = getattr(instance, '_old_priority', None)
    if old_priority and instance.priority != old_priority:
        try:
            NotificationService.notify_priority_change(instance, old_priority)
        except Exception as e:
            logger.error(f'Notification error on priority change: {e}')


@receiver(post_save, sender=TicketComment)
def comment_post_save(sender, instance, created, **kwargs):
    """Notify relevant parties when a comment is added."""
    if created and instance.comment_type != 'system':
        try:
            from notifications.services.notification_service import NotificationService
            NotificationService.notify_new_comment(instance)
        except Exception as e:
            logger.error(f'Notification error on comment: {e}')
