"""\nJeyaRamaDesk — Reports Admin\n"""

from django.contrib import admin
from .models import SavedReport


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'created_at']
    list_filter = ['report_type']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
