"""
JeyaRamaDesk — Notification Service
Centralised helper for creating notifications and optionally
pushing them to the connected WebSocket consumer.
"""

import logging
from django.conf import settings
from notifications.models import Notification

logger = logging.getLogger('jeyaramadesk')


class NotificationService:
    """Facade for notification creation and delivery."""

    # ── Core CRUD ─────────────────────────────────────────────

    @staticmethod
    def create_notification(*, user, title, message='', notification_type='system', ticket=None):
        """
        Create a persisted notification and attempt real-time push.

        Args:
            user: recipient User instance
            title: short headline
            message: longer body (optional)
            notification_type: one of Notification.NotificationType values
            ticket: related Ticket instance (optional)

        Returns:
            Notification instance
        """
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            ticket=ticket,
        )
        # Attempt WebSocket push (fail silently if Channels unavailable)
        NotificationService._push_realtime(notification)
        logger.info(f'Notification created: "{title}" → {user.email}')
        return notification

    @staticmethod
    def get_unread_count(user):
        """Return the number of unread notifications for a user."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def get_recent(user, limit=20):
        """Return the most recent notifications for a user."""
        return Notification.objects.filter(user=user)[:limit]

    # ── Convenience helpers (used by signals / automation) ────

    @staticmethod
    def notify_new_ticket(ticket):
        """Notify managers and superadmins about a new ticket."""
        from accounts.models import User
        staff = User.objects.filter(
            role__in=['superadmin', 'manager'],
            is_active=True,
        )
        for user in staff:
            NotificationService.create_notification(
                user=user,
                title='New Ticket Created',
                message=f'Ticket {ticket.ticket_id}: {ticket.title}',
                notification_type='ticket_created',
                ticket=ticket,
            )

    @staticmethod
    def notify_new_comment(comment):
        """Notify the ticket owner, assigned agent, and admins about a new comment."""
        ticket = comment.ticket
        recipients = set()

        # Notify ticket customer (unless they wrote the comment)
        if ticket.customer and ticket.customer != comment.author:
            recipients.add(ticket.customer)

        # Notify assigned agent (unless they wrote the comment)
        if ticket.assigned_agent and ticket.assigned_agent != comment.author:
            recipients.add(ticket.assigned_agent)

        # If the commenter is a customer, also notify managers / superadmins
        if comment.author and hasattr(comment.author, 'is_customer') and comment.author.is_customer:
            from accounts.models import User
            staff = User.objects.filter(
                role__in=['superadmin', 'manager'],
                is_active=True,
            ).exclude(pk=comment.author.pk)
            recipients.update(staff)

        for user in recipients:
            NotificationService.create_notification(
                user=user,
                title='New Comment',
                message=f'{comment.author.full_name or comment.author.email} commented on {ticket.ticket_id}',
                notification_type='comment_added',
                ticket=ticket,
            )

    @staticmethod
    def notify_ticket_assigned(ticket):
        """Notify the assigned agent about their new assignment."""
        if ticket.assigned_agent:
            NotificationService.create_notification(
                user=ticket.assigned_agent,
                title='Ticket Assigned to You',
                message=f'You have been assigned ticket {ticket.ticket_id}: {ticket.title}',
                notification_type='ticket_assigned',
                ticket=ticket,
            )

    @staticmethod
    def notify_sla_breach(ticket, breach_type='response'):
        """Notify agent and managers about an SLA breach."""
        from accounts.models import User

        message = f'SLA {breach_type} breach on ticket {ticket.ticket_id}'
        recipients = set()

        if ticket.assigned_agent:
            recipients.add(ticket.assigned_agent)

        managers = User.objects.filter(role__in=['superadmin', 'manager'], is_active=True)
        recipients.update(managers)

        for user in recipients:
            NotificationService.create_notification(
                user=user,
                title='SLA Breach Alert',
                message=message,
                notification_type='sla_breach',
                ticket=ticket,
            )

    @staticmethod
    def notify_status_change(ticket, old_status):
        """Notify customer and assigned agent when ticket status changes."""
        recipients = set()

        # Notify the customer who raised the ticket
        if ticket.customer:
            recipients.add(ticket.customer)

        # Notify the assigned agent
        if ticket.assigned_agent:
            recipients.add(ticket.assigned_agent)

        display_old = old_status.replace('_', ' ').title()
        display_new = ticket.status.replace('_', ' ').title()

        for user in recipients:
            NotificationService.create_notification(
                user=user,
                title='Ticket Status Updated',
                message=f'Ticket {ticket.ticket_id} status changed from {display_old} to {display_new}.',
                notification_type='status_change',
                ticket=ticket,
            )

    @staticmethod
    def notify_priority_change(ticket, old_priority):
        """Notify customer and assigned agent when ticket priority changes."""
        recipients = set()

        if ticket.customer:
            recipients.add(ticket.customer)

        if ticket.assigned_agent:
            recipients.add(ticket.assigned_agent)

        for user in recipients:
            NotificationService.create_notification(
                user=user,
                title='Ticket Priority Changed',
                message=f'Ticket {ticket.ticket_id} priority changed from {old_priority.title()} to {ticket.priority.title()}.',
                notification_type='priority_change',
                ticket=ticket,
            )

    # ── WebSocket push ────────────────────────────────────────

    @staticmethod
    def _push_realtime(notification):
        """
        Push a notification to the user's WebSocket channel group.
        Fails silently if Channels / Redis is unavailable.
        """
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer is None:
                return

            group_name = f'notifications_{notification.user.id}'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'notification': {
                        'id': str(notification.id),
                        'title': notification.title,
                        'message': notification.message,
                        'type': notification.notification_type,
                        'ticket_id': str(notification.ticket_id) if notification.ticket_id else None,
                        'created_at': notification.created_at.isoformat(),
                    },
                },
            )
        except Exception as e:
            logger.debug(f'WebSocket push skipped: {e}')
