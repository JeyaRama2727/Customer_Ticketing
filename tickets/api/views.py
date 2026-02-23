"""
JeyaRamaDesk — Ticket API Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from tickets.models import Ticket, TicketComment, Category, Tag
from tickets.api.serializers import (
    TicketListSerializer, TicketDetailSerializer, TicketCreateSerializer,
    TicketCommentSerializer, CategorySerializer, TagSerializer,
)
from tickets.services.ticket_service import TicketService
from accounts.permissions import IsStaffMember


class TicketViewSet(viewsets.ModelViewSet):
    """API endpoint for tickets."""

    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'priority', 'category', 'assigned_agent', 'is_escalated']
    search_fields = ['ticket_id', 'title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('customer', 'assigned_agent', 'category')
        if user.role == 'customer':
            return qs.filter(customer=user)
        elif user.role == 'agent':
            return qs.filter(assigned_agent=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data
        TicketService.create_ticket(data, self.request.user)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Add a comment to a ticket."""
        ticket = self.get_object()
        content = request.data.get('content', '')
        comment_type = request.data.get('comment_type', 'reply')
        if request.user.role == 'customer':
            comment_type = 'reply'
        comment = TicketService.add_comment(ticket, request.user, content, comment_type)
        return Response(TicketCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """List comments for a ticket."""
        ticket = self.get_object()
        comments = ticket.comments.select_related('author').all()
        if request.user.role == 'customer':
            comments = comments.exclude(comment_type='internal_note')
        serializer = TicketCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffMember])
    def assign(self, request, pk=None):
        """Assign ticket to an agent."""
        ticket = self.get_object()
        from accounts.models import User
        agent_id = request.data.get('agent_id')
        agent = User.objects.get(pk=agent_id) if agent_id else None
        TicketService.assign_ticket(ticket, agent, request.user)
        return Response({'status': 'assigned'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffMember])
    def escalate(self, request, pk=None):
        """Escalate a ticket."""
        ticket = self.get_object()
        reason = request.data.get('reason', '')
        TicketService.escalate_ticket(ticket, request.user, reason)
        return Response({'status': 'escalated'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get ticket statistics."""
        stats = TicketService.get_ticket_stats(request.user)
        return Response(stats)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name']


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']
