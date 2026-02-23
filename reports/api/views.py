"""
JeyaRamaDesk — Reports API Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from accounts.permissions import IsStaffMember
from tickets.models import Ticket
from sla.models import SLABreach


class TicketSummaryAPI(APIView):
    """API endpoint for ticket summary report data."""
    permission_classes = [IsAuthenticated, IsStaffMember]

    def get(self, request):
        now = timezone.now()
        date_from = request.query_params.get('date_from', (now - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.query_params.get('date_to', now.strftime('%Y-%m-%d'))

        tickets = Ticket.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        summary = tickets.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            resolved=Count('id', filter=Q(status__in=['resolved', 'closed'])),
        )

        by_priority = list(tickets.values('priority').annotate(count=Count('id')))
        by_status = list(tickets.values('status').annotate(count=Count('id')))

        return Response({
            'summary': summary,
            'by_priority': by_priority,
            'by_status': by_status,
            'date_from': date_from,
            'date_to': date_to,
        })
