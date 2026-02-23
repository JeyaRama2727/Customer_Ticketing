"""
JeyaRamaDesk — Dashboard API Views
REST API endpoint for dashboard statistics.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


class DashboardStatsAPI(APIView):
    """API endpoint returning dashboard statistics as JSON."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tickets.models import Ticket
        from sla.models import SLABreach

        user = request.user
        now = timezone.now()
        last_7 = now - timedelta(days=7)

        if user.is_customer:
            tickets = Ticket.objects.filter(customer=user)
        elif hasattr(user, 'is_agent') and user.is_agent:
            tickets = Ticket.objects.filter(
                Q(assigned_agent=user) | Q(customer=user)
            )
        else:
            tickets = Ticket.objects.all()

        stats = tickets.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            resolved=Count('id', filter=Q(status__in=['resolved', 'closed'])),
            urgent=Count('id', filter=Q(priority='urgent')),
        )

        stats['new_this_week'] = tickets.filter(created_at__gte=last_7).count()

        if user.is_staff_member:
            stats['sla_breaches'] = SLABreach.objects.filter(
                breached_at__gte=last_7
            ).count()

        return Response(stats)
