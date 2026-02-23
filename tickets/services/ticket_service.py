"""
JeyaRamaDesk — Ticket Service Layer
Business logic for the ticketing system.
"""

import logging
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from tickets.models import (
    Ticket, TicketComment, TicketAttachment, TicketActivity, Category,
)

logger = logging.getLogger('jeyaramadesk')


class TicketService:
    """Core business logic for ticket operations."""

    @staticmethod
    @transaction.atomic
    def create_ticket(data, customer, files=None):
        """
        Create a new ticket with optional attachments.
        Applies SLA policy based on priority and runs automation rules.
        """
        ticket = Ticket.objects.create(
            title=data['title'],
            description=data['description'],
            customer=customer,
            category_id=data.get('category') or None,
            priority=data.get('priority', Ticket.Priority.MEDIUM),
            source=data.get('source', 'web'),
            due_date=data.get('due_date') or None,
        )

        # Create activity
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type=TicketActivity.ActivityType.CREATED,
            actor=customer,
            description=f'Ticket {ticket.ticket_id} created.',
        )

        # Handle file attachments
        if files:
            TicketService._process_attachments(ticket, None, files, customer)

        # Apply SLA policy
        TicketService._apply_sla(ticket)

        # Run automation rules
        try:
            from automation.services.automation_service import AutomationService
            AutomationService.run_ticket_automations(ticket)
        except Exception as e:
            logger.error(f'Automation error for ticket {ticket.ticket_id}: {e}')

        logger.info(f'Ticket created: {ticket.ticket_id} by {customer.email}')
        return ticket

    @staticmethod
    @transaction.atomic
    def update_ticket(ticket, data, actor):
        """Update ticket fields and track changes."""
        changes = []

        # Status change
        new_status = data.get('status')
        if new_status and new_status != ticket.status:
            old_status = ticket.status
            ticket.status = new_status
            changes.append(('status_changed', old_status, new_status))

            if new_status == Ticket.Status.RESOLVED:
                ticket.resolved_at = timezone.now()
                if ticket.sla_resolution_deadline:
                    ticket.sla_resolution_met = timezone.now() <= ticket.sla_resolution_deadline

        # Priority change
        new_priority = data.get('priority')
        if new_priority and new_priority != ticket.priority:
            old_priority = ticket.priority
            ticket.priority = new_priority
            changes.append(('priority_changed', old_priority, new_priority))

        # Assignment change
        new_agent_id = data.get('assigned_agent')
        if new_agent_id is not None:
            from accounts.models import User
            old_agent = ticket.assigned_agent
            if new_agent_id == '':
                ticket.assigned_agent = None
            else:
                ticket.assigned_agent = User.objects.get(pk=new_agent_id)

            if old_agent != ticket.assigned_agent:
                old_val = old_agent.full_name if old_agent else 'Unassigned'
                new_val = ticket.assigned_agent.full_name if ticket.assigned_agent else 'Unassigned'
                activity_type = 'reassigned' if old_agent else 'assigned'
                changes.append((activity_type, old_val, new_val))

        # Category change
        new_cat = data.get('category')
        if new_cat is not None:
            old_cat = ticket.category
            if new_cat == '':
                ticket.category = None
            else:
                ticket.category_id = new_cat
            if old_cat != ticket.category:
                changes.append(('category_changed',
                                old_cat.name if old_cat else 'None',
                                ticket.category.name if ticket.category else 'None'))

        # Title/description
        if 'title' in data:
            ticket.title = data['title']
        if 'description' in data:
            ticket.description = data['description']
        if 'due_date' in data:
            ticket.due_date = data['due_date'] or None

        ticket.save()

        # Record activities
        for activity_type, old_val, new_val in changes:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type=activity_type,
                actor=actor,
                old_value=str(old_val),
                new_value=str(new_val),
                description=f'{activity_type.replace("_", " ").title()}: {old_val} → {new_val}',
            )

        return ticket

    @staticmethod
    @transaction.atomic
    def add_comment(ticket, author, content, comment_type='reply', files=None):
        """Add a comment/reply/internal note to a ticket."""
        comment = TicketComment.objects.create(
            ticket=ticket,
            author=author,
            content=content,
            comment_type=comment_type,
        )

        # Track first response for SLA
        if (comment_type == 'reply'
                and author.is_staff_member
                and not ticket.first_response_at):
            ticket.first_response_at = timezone.now()
            if ticket.sla_response_deadline:
                ticket.sla_response_met = timezone.now() <= ticket.sla_response_deadline
            ticket.save(update_fields=['first_response_at', 'sla_response_met'])

        # Activity
        activity_type = (
            TicketActivity.ActivityType.NOTE_ADDED
            if comment_type == 'internal_note'
            else TicketActivity.ActivityType.COMMENTED
        )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type=activity_type,
            actor=author,
            description=f'{author.full_name} added a {comment.get_comment_type_display().lower()}.',
        )

        # Attachments
        if files:
            TicketService._process_attachments(ticket, comment, files, author)

        return comment

    @staticmethod
    @transaction.atomic
    def assign_ticket(ticket, agent, actor):
        """Assign a ticket to an agent."""
        old_agent = ticket.assigned_agent
        ticket.assigned_agent = agent
        ticket.save(update_fields=['assigned_agent', 'updated_at'])

        TicketActivity.objects.create(
            ticket=ticket,
            activity_type=(
                TicketActivity.ActivityType.REASSIGNED if old_agent
                else TicketActivity.ActivityType.ASSIGNED
            ),
            actor=actor,
            old_value=old_agent.full_name if old_agent else 'Unassigned',
            new_value=agent.full_name if agent else 'Unassigned',
            description=f'Ticket assigned to {agent.full_name}.' if agent else 'Ticket unassigned.',
        )
        return ticket

    @staticmethod
    @transaction.atomic
    def escalate_ticket(ticket, actor=None, reason=''):
        """Escalate a ticket."""
        ticket.is_escalated = True
        ticket.escalation_level += 1
        ticket.save(update_fields=['is_escalated', 'escalation_level', 'updated_at'])

        TicketActivity.objects.create(
            ticket=ticket,
            activity_type=TicketActivity.ActivityType.ESCALATED,
            actor=actor,
            description=f'Ticket escalated to level {ticket.escalation_level}. {reason}',
        )

        logger.warning(f'Ticket {ticket.ticket_id} escalated to level {ticket.escalation_level}')
        return ticket

    @staticmethod
    def _process_attachments(ticket, comment, files, uploader):
        """Process and save file attachments."""
        for f in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                comment=comment,
                file=f,
                filename=f.name,
                file_size=f.size,
                content_type=getattr(f, 'content_type', ''),
                uploaded_by=uploader,
            )

    @staticmethod
    def _apply_sla(ticket):
        """Apply SLA policy to a ticket based on priority."""
        try:
            from sla.models import SLAPolicy
            policy = SLAPolicy.objects.filter(
                priority=ticket.priority, is_active=True,
            ).first()
            if policy:
                ticket.sla_policy = policy
                now = timezone.now()
                ticket.sla_response_deadline = now + timezone.timedelta(
                    hours=policy.response_time_hours
                )
                ticket.sla_resolution_deadline = now + timezone.timedelta(
                    hours=policy.resolution_time_hours
                )
                ticket.save(update_fields=[
                    'sla_policy', 'sla_response_deadline', 'sla_resolution_deadline',
                ])
        except Exception as e:
            logger.error(f'SLA apply error: {e}')

    @staticmethod
    def get_ticket_stats(user=None):
        """Get ticket counts grouped by status."""
        from django.db.models import Count, Q

        qs = Ticket.objects.all()
        if user and user.role == 'customer':
            qs = qs.filter(customer=user)
        elif user and user.role == 'agent':
            qs = qs.filter(assigned_agent=user)

        return qs.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            pending=Count('id', filter=Q(status='pending')),
            resolved=Count('id', filter=Q(status='resolved')),
            closed=Count('id', filter=Q(status='closed')),
            urgent=Count('id', filter=Q(priority='urgent')),
            escalated=Count('id', filter=Q(is_escalated=True)),
        )
