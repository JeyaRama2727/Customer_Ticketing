"""JeyaRamaDesk — Notification API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from notifications.models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and managing the authenticated user's notifications.

    list   — GET  /api/notifications/
    detail — GET  /api/notifications/{id}/
    read   — POST /api/notifications/{id}/read/
    mark_all_read — POST /api/notifications/mark-all-read/
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() in ('true', '1'))
        return qs

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_read()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all unread notifications as read."""
        count = Notification.objects.filter(
            user=request.user, is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': count})
