"""
JeyaRamaDesk — SLA Admin
"""

from django.contrib import admin
from .models import SLAPolicy, SLABreach


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'response_time_hours', 'resolution_time_hours', 'is_active')
    list_filter = ('priority', 'is_active')
    search_fields = ('name',)


@admin.register(SLABreach)
class SLABreachAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'breach_type', 'deadline', 'breached_at', 'notified')
    list_filter = ('breach_type', 'notified', 'breached_at')
    readonly_fields = ('ticket', 'policy', 'breach_type', 'deadline', 'breached_at')
    list_per_page = 50
