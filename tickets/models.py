"""
JeyaRamaDesk — Ticket Models
Core ticketing system with full lifecycle tracking.
Indexed for high-performance queries at scale (millions of records).
"""

import uuid
import random
import string
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def generate_ticket_id():
    """Generate a unique ticket ID like JRD-A3X9K2."""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=6))
    return f'JRD-{code}'


class Category(models.Model):
    """Ticket categories for organization and routing."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    color = models.CharField(max_length=7, default='#6366f1', help_text='Hex color code')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jrd_categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tags for ticket classification."""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#8b5cf6')

    class Meta:
        db_table = 'jrd_tags'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """
    Core Ticket model — the heart of JeyaRamaDesk.
    Designed for millions of records with comprehensive indexing.
    """

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        PENDING = 'pending', 'Pending'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    # ── Identity ──────────────────────────────────────────────
    id = models.BigAutoField(primary_key=True)
    ticket_id = models.CharField(
        max_length=20, unique=True, default=generate_ticket_id,
        db_index=True, editable=False,
    )

    # ── Content ───────────────────────────────────────────────
    title = models.CharField(max_length=300)
    description = models.TextField(help_text='Rich text description of the issue')

    # ── Classification ────────────────────────────────────────
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets', db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, db_index=True,
    )
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.OPEN, db_index=True,
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='tickets')

    # ── People ────────────────────────────────────────────────
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='submitted_tickets', db_index=True,
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets',
        db_index=True,
    )

    # ── SLA & Timing ─────────────────────────────────────────
    sla_policy = models.ForeignKey(
        'sla.SLAPolicy', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets',
    )
    sla_response_deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    sla_resolution_deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    sla_response_met = models.BooleanField(null=True, blank=True)
    sla_resolution_met = models.BooleanField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    # ── Metadata ──────────────────────────────────────────────
    source = models.CharField(
        max_length=20, default='web',
        choices=[('web', 'Web'), ('email', 'Email'), ('api', 'API'), ('phone', 'Phone')],
    )
    is_escalated = models.BooleanField(default=False, db_index=True)
    escalation_level = models.PositiveSmallIntegerField(default=0)
    csat_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Customer satisfaction 1-5',
    )
    csat_feedback = models.TextField(blank=True, default='')

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jrd_tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority'], name='idx_ticket_status_prio'),
            models.Index(fields=['customer', 'status'], name='idx_ticket_cust_status'),
            models.Index(fields=['assigned_agent', 'status'], name='idx_ticket_agent_status'),
            models.Index(fields=['category', 'status'], name='idx_ticket_cat_status'),
            models.Index(fields=['created_at', 'status'], name='idx_ticket_created_status'),
            models.Index(fields=['sla_response_deadline'], name='idx_ticket_sla_resp'),
            models.Index(fields=['sla_resolution_deadline'], name='idx_ticket_sla_resol'),
            models.Index(fields=['is_escalated', 'status'], name='idx_ticket_escalated'),
        ]

    def __str__(self):
        return f'{self.ticket_id}: {self.title}'

    @property
    def is_overdue(self):
        if self.due_date and self.status not in (self.Status.RESOLVED, self.Status.CLOSED):
            return timezone.now() > self.due_date
        return False

    @property
    def sla_response_breached(self):
        if self.sla_response_deadline and not self.first_response_at:
            return timezone.now() > self.sla_response_deadline
        return False

    @property
    def sla_resolution_breached(self):
        if self.sla_resolution_deadline and self.status not in (self.Status.RESOLVED, self.Status.CLOSED):
            return timezone.now() > self.sla_resolution_deadline
        return False

    @property
    def priority_color(self):
        return {
            'low': '#10b981', 'medium': '#f59e0b',
            'high': '#f97316', 'urgent': '#ef4444',
        }.get(self.priority, '#6b7280')

    @property
    def status_color(self):
        return {
            'open': '#3b82f6', 'in_progress': '#8b5cf6',
            'pending': '#f59e0b', 'resolved': '#10b981',
            'closed': '#6b7280',
        }.get(self.status, '#6b7280')


class TicketComment(models.Model):
    """Threaded conversation on tickets — both public replies and internal notes."""

    class CommentType(models.TextChoices):
        REPLY = 'reply', 'Reply'
        INTERNAL_NOTE = 'internal_note', 'Internal Note'
        SYSTEM = 'system', 'System'

    id = models.BigAutoField(primary_key=True)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='comments', db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='ticket_comments',
    )
    content = models.TextField()
    comment_type = models.CharField(
        max_length=15, choices=CommentType.choices, default=CommentType.REPLY,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jrd_ticket_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'comment_type'], name='idx_comment_ticket_type'),
        ]

    def __str__(self):
        return f'Comment on {self.ticket.ticket_id} by {self.author}'


class TicketAttachment(models.Model):
    """File attachments for tickets and comments."""

    id = models.BigAutoField(primary_key=True)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='attachments',
    )
    comment = models.ForeignKey(
        TicketComment, on_delete=models.CASCADE,
        null=True, blank=True, related_name='attachments',
    )
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0, help_text='Size in bytes')
    content_type = models.CharField(max_length=100, blank=True, default='')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jrd_ticket_attachments'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename

    @property
    def file_size_display(self):
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        return f'{self.file_size / (1024 * 1024):.1f} MB'


class TicketActivity(models.Model):
    """
    Activity timeline tracking all changes on a ticket.
    Provides a complete audit trail.
    """

    class ActivityType(models.TextChoices):
        CREATED = 'created', 'Created'
        STATUS_CHANGED = 'status_changed', 'Status Changed'
        PRIORITY_CHANGED = 'priority_changed', 'Priority Changed'
        ASSIGNED = 'assigned', 'Assigned'
        REASSIGNED = 'reassigned', 'Reassigned'
        COMMENTED = 'commented', 'Commented'
        NOTE_ADDED = 'note_added', 'Note Added'
        ESCALATED = 'escalated', 'Escalated'
        SLA_BREACHED = 'sla_breached', 'SLA Breached'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
        REOPENED = 'reopened', 'Reopened'
        ATTACHMENT_ADDED = 'attachment_added', 'Attachment Added'
        TAG_ADDED = 'tag_added', 'Tag Added'
        CATEGORY_CHANGED = 'category_changed', 'Category Changed'

    id = models.BigAutoField(primary_key=True)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='activities', db_index=True,
    )
    activity_type = models.CharField(
        max_length=20, choices=ActivityType.choices, db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    old_value = models.CharField(max_length=255, blank=True, default='')
    new_value = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'jrd_ticket_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket', 'activity_type'], name='idx_activity_ticket_type'),
            models.Index(fields=['ticket', 'created_at'], name='idx_activity_ticket_time'),
        ]

    def __str__(self):
        return f'{self.activity_type} on {self.ticket.ticket_id}'
