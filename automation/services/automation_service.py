"""
JeyaRamaDesk — Automation Service
Core engine that evaluates and executes automation rules against tickets.
"""

import logging
from django.utils import timezone

from automation.models import AutomationRule, AutomationLog
from tickets.models import Ticket, TicketActivity

logger = logging.getLogger('jeyaramadesk')


class AutomationService:
    """Service class for evaluating and executing automation rules."""

    @staticmethod
    def run_rules(trigger_event, ticket):
        """
        Evaluate all active rules for a given trigger event against a ticket.
        Rules are evaluated in priority_order; stops if a rule has stop_processing=True.
        """
        rules = AutomationRule.objects.filter(
            trigger_event=trigger_event,
            is_active=True,
        ).order_by('priority_order')

        for rule in rules:
            if AutomationService._match_conditions(rule, ticket):
                success = AutomationService._execute_action(rule, ticket)

                # Log the execution
                AutomationLog.objects.create(
                    rule=rule,
                    ticket=ticket,
                    status=AutomationLog.Status.SUCCESS if success else AutomationLog.Status.FAILED,
                    action_taken=f'{rule.get_action_type_display()} executed',
                    error_message='' if success else 'Action execution failed',
                )

                if rule.stop_processing:
                    break

    @staticmethod
    def _match_conditions(rule, ticket):
        """
        Check if a ticket matches the rule's conditions.
        Conditions is a JSON dict where keys map to ticket fields.
        """
        conditions = rule.conditions
        if not conditions:
            return True  # No conditions = always match

        try:
            for field, expected_value in conditions.items():
                # Handle nested lookups (e.g., "category__name")
                if '__' in field:
                    parts = field.split('__')
                    obj = ticket
                    for part in parts:
                        obj = getattr(obj, part, None)
                    actual_value = obj
                else:
                    actual_value = getattr(ticket, field, None)

                # Handle FK objects — compare by string or id
                if hasattr(actual_value, 'pk'):
                    actual_value = str(actual_value.pk)

                if str(actual_value).lower() != str(expected_value).lower():
                    return False
            return True
        except Exception as e:
            logger.error(f'Automation condition match error: {e}')
            return False

    @staticmethod
    def _execute_action(rule, ticket):
        """Execute the action defined in the automation rule."""
        try:
            action_type = rule.action_type
            params = rule.action_params or {}

            if action_type == AutomationRule.ActionType.ASSIGN_AGENT:
                return AutomationService._action_assign_agent(ticket, params)
            elif action_type == AutomationRule.ActionType.CHANGE_PRIORITY:
                return AutomationService._action_change_priority(ticket, params)
            elif action_type == AutomationRule.ActionType.CHANGE_STATUS:
                return AutomationService._action_change_status(ticket, params)
            elif action_type == AutomationRule.ActionType.ADD_TAG:
                return AutomationService._action_add_tag(ticket, params)
            elif action_type == AutomationRule.ActionType.ESCALATE:
                return AutomationService._action_escalate(ticket, params)
            elif action_type == AutomationRule.ActionType.ADD_COMMENT:
                return AutomationService._action_add_comment(ticket, params)
            elif action_type == AutomationRule.ActionType.SEND_NOTIFICATION:
                return AutomationService._action_send_notification(ticket, params)
            else:
                logger.warning(f'Unknown action type: {action_type}')
                return False
        except Exception as e:
            logger.error(f'Automation action error: {e}')
            return False

    @staticmethod
    def _action_assign_agent(ticket, params):
        """Assign ticket to a specific agent."""
        from accounts.models import User
        agent_id = params.get('agent_id')
        if not agent_id:
            return False
        try:
            agent = User.objects.get(pk=agent_id, role__in=['agent', 'manager', 'superadmin'])
            ticket.assigned_agent = agent
            ticket.status = 'assigned'
            ticket.save(update_fields=['assigned_agent', 'status', 'updated_at'])

            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='assigned',
                description=f'Auto-assigned to {agent.full_name} by automation rule',
            )
            return True
        except User.DoesNotExist:
            return False

    @staticmethod
    def _action_change_priority(ticket, params):
        """Change ticket priority."""
        new_priority = params.get('priority')
        if new_priority not in dict(Ticket.Priority.choices):
            return False
        old_priority = ticket.priority
        ticket.priority = new_priority
        ticket.save(update_fields=['priority', 'updated_at'])

        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='priority_changed',
            old_value=old_priority,
            new_value=new_priority,
            description=f'Priority changed from {old_priority} to {new_priority} by automation',
        )
        return True

    @staticmethod
    def _action_change_status(ticket, params):
        """Change ticket status."""
        new_status = params.get('status')
        if new_status not in dict(Ticket.Status.choices):
            return False
        old_status = ticket.status
        ticket.status = new_status
        if new_status in ('resolved', 'closed'):
            ticket.resolved_at = timezone.now()
        ticket.save(update_fields=['status', 'resolved_at', 'updated_at'])

        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='status_changed',
            old_value=old_status,
            new_value=new_status,
            description=f'Status changed from {old_status} to {new_status} by automation',
        )
        return True

    @staticmethod
    def _action_add_tag(ticket, params):
        """Add a tag to the ticket."""
        from tickets.models import Tag
        tag_name = params.get('tag')
        if not tag_name:
            return False
        tag, _ = Tag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': tag_name.lower().replace(' ', '-')},
        )
        ticket.tags.add(tag)
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='tag_added',
            new_value=tag_name,
            description=f'Tag "{tag_name}" added by automation',
        )
        return True

    @staticmethod
    def _action_escalate(ticket, params):
        """Escalate the ticket."""
        ticket.is_escalated = True
        ticket.escalation_level = min(ticket.escalation_level + 1, 3)
        ticket.save(update_fields=['is_escalated', 'escalation_level', 'updated_at'])

        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='escalated',
            description=f'Escalated to level {ticket.escalation_level} by automation',
        )
        return True

    @staticmethod
    def _action_add_comment(ticket, params):
        """Add an internal note to the ticket."""
        from tickets.models import TicketComment
        message = params.get('message', 'Automated internal note')
        TicketComment.objects.create(
            ticket=ticket,
            comment_type='internal_note',
            body=message,
        )
        return True

    @staticmethod
    def _action_send_notification(ticket, params):
        """Send a notification (delegates to notification service)."""
        try:
            from notifications.services.notification_service import NotificationService
            message = params.get('message', f'Automation triggered for ticket {ticket.ticket_id}')
            recipients = params.get('recipients', 'agent')

            if recipients == 'agent' and ticket.assigned_agent:
                NotificationService.create_notification(
                    user=ticket.assigned_agent,
                    title='Automation Alert',
                    message=message,
                    notification_type='automation',
                    ticket=ticket,
                )
            elif recipients == 'customer' and ticket.customer:
                NotificationService.create_notification(
                    user=ticket.customer,
                    title='Ticket Update',
                    message=message,
                    notification_type='automation',
                    ticket=ticket,
                )
            return True
        except Exception as e:
            logger.error(f'Notification action error: {e}')
            return False

    @staticmethod
    def get_rule_stats():
        """Return automation rule statistics."""
        from django.db.models import Count, Q

        total_rules = AutomationRule.objects.count()
        active_rules = AutomationRule.objects.filter(is_active=True).count()

        log_stats = AutomationLog.objects.aggregate(
            total_executions=Count('id'),
            successful=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
        )

        return {
            'total_rules': total_rules,
            'active_rules': active_rules,
            'total_executions': log_stats['total_executions'],
            'successful_executions': log_stats['successful'],
            'failed_executions': log_stats['failed'],
        }
