"""
JeyaRamaDesk — Automation API Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsStaffMember, IsSuperAdmin
from automation.models import AutomationRule, AutomationLog
from automation.services.automation_service import AutomationService
from .serializers import AutomationRuleSerializer, AutomationLogSerializer


class AutomationRuleViewSet(viewsets.ModelViewSet):
    """CRUD API for automation rules."""
    queryset = AutomationRule.objects.all().order_by('priority_order')
    serializer_class = AutomationRuleSerializer
    permission_classes = [IsAuthenticated, IsStaffMember]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return automation rule statistics."""
        stats = AutomationService.get_rule_stats()
        return Response(stats, status=status.HTTP_200_OK)


class AutomationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for automation logs."""
    queryset = AutomationLog.objects.select_related(
        'rule', 'ticket'
    ).order_by('-executed_at')
    serializer_class = AutomationLogSerializer
    permission_classes = [IsAuthenticated, IsStaffMember]
    filterset_fields = ['status']
