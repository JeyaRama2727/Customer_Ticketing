"""
JeyaRamaDesk — Ticket API Serializers
"""

from rest_framework import serializers
from tickets.models import Ticket, TicketComment, TicketAttachment, TicketActivity, Category, Tag
from accounts.api.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'color', 'is_active']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color']


class TicketListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    agent_name = serializers.CharField(source='assigned_agent.full_name', read_only=True, default=None)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_id', 'title', 'status', 'priority',
            'customer', 'customer_name', 'assigned_agent', 'agent_name',
            'category', 'category_name', 'is_escalated',
            'created_at', 'updated_at',
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    assigned_agent = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'due_date']


class TicketCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'author', 'content', 'comment_type', 'created_at']
        read_only_fields = ['id', 'ticket', 'author', 'created_at']


class TicketActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.full_name', read_only=True, default=None)

    class Meta:
        model = TicketActivity
        fields = [
            'id', 'activity_type', 'actor', 'actor_name',
            'old_value', 'new_value', 'description', 'created_at',
        ]
