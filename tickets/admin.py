"""
JeyaRamaDesk — Ticket Admin Configuration
"""

from django.contrib import admin
from .models import Ticket, TicketComment, TicketAttachment, TicketActivity, Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('author', 'comment_type', 'created_at')


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ('filename', 'file_size', 'uploaded_by', 'uploaded_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id', 'title', 'customer', 'assigned_agent',
        'status', 'priority', 'category', 'created_at',
    )
    list_filter = ('status', 'priority', 'category', 'is_escalated', 'created_at')
    search_fields = ('ticket_id', 'title', 'customer__email', 'assigned_agent__email')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
    list_per_page = 25
    date_hierarchy = 'created_at'
    inlines = [TicketCommentInline, TicketAttachmentInline]

    actions = ['mark_resolved', 'mark_closed', 'escalate_tickets']

    @admin.action(description='Mark selected tickets as Resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(status=Ticket.Status.RESOLVED, resolved_at=__import__('django.utils.timezone', fromlist=['now']).now())

    @admin.action(description='Mark selected tickets as Closed')
    def mark_closed(self, request, queryset):
        queryset.update(status=Ticket.Status.CLOSED)

    @admin.action(description='Escalate selected tickets')
    def escalate_tickets(self, request, queryset):
        queryset.update(is_escalated=True)


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'activity_type', 'actor', 'created_at')
    list_filter = ('activity_type', 'created_at')
    readonly_fields = ('ticket', 'activity_type', 'actor', 'old_value', 'new_value', 'description', 'created_at')
    list_per_page = 50
