"""JeyaRamaDesk — Notification Admin"""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('id', 'created_at', 'read_at')
    list_per_page = 50
    raw_id_fields = ('user', 'ticket')
    date_hierarchy = 'created_at'

    actions = ['mark_read', 'mark_unread']

    @admin.action(description='Mark selected as read')
    def mark_read(self, request, queryset):
        from django.utils import timezone
        queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())

    @admin.action(description='Mark selected as unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
