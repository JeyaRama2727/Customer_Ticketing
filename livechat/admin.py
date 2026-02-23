"""JeyaRamaDesk — Live Chat Admin"""

from django.contrib import admin
from .models import ChatRoom, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('id', 'sender', 'content', 'message_type', 'created_at')


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'customer', 'agent', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'customer__email', 'agent__email')
    raw_id_fields = ('customer', 'agent', 'ticket')
    inlines = [ChatMessageInline]
    list_per_page = 30


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('content', 'sender__email')
    raw_id_fields = ('room', 'sender')
    readonly_fields = ('id', 'created_at')
