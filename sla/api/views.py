"""
JeyaRamaDesk — SLA API Views
REST API endpoints for SLA policies and breach management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsStaffMember
from sla.models import SLAPolicy, SLABreach
from sla.services.sla_service import SLAService
from .serializers import SLAPolicySerializer, SLABreachSerializer


class SLAPolicyViewSet(viewsets.ModelViewSet):
    """
    CRUD API for SLA policies.
    Only staff members can manage SLA policies.
    """
    queryset = SLAPolicy.objects.all().order_by('-created_at')
    serializer_class = SLAPolicySerializer
    permission_classes = [IsAuthenticated, IsStaffMember]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return SLA compliance statistics."""
        stats = SLAService.get_sla_stats()
        return Response(stats, status=status.HTTP_200_OK)


class SLABreachViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for SLA breach records.
    Staff members can view breach history.
    """
    queryset = SLABreach.objects.select_related(
        'ticket', 'policy'
    ).order_by('-breached_at')
    serializer_class = SLABreachSerializer
    permission_classes = [IsAuthenticated, IsStaffMember]
    filterset_fields = ['breach_type', 'notified']
