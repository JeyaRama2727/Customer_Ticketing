"""
JeyaRamaDesk — Dashboard Views
Main analytics dashboard with ticket stats, agent performance,
SLA compliance, and trend charts.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta


@login_required
def dashboard_index_view(request):
    """Main dashboard view with role-based analytics."""
    from tickets.models import Ticket, TicketActivity
    from accounts.models import User
    from sla.models import SLABreach

    user = request.user
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    # ── Base queryset (role-based) ────────────────────────
    if user.is_customer:
        tickets = Ticket.objects.filter(customer=user)
    elif user.is_agent:
        tickets = Ticket.objects.filter(
            Q(assigned_agent=user) | Q(customer=user)
        )
    else:
        tickets = Ticket.objects.all()

    # ── Ticket Stats ──────────────────────────────────────
    ticket_stats = tickets.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        assigned=Count('id', filter=Q(status='assigned')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        resolved=Count('id', filter=Q(status='resolved')),
        closed=Count('id', filter=Q(status='closed')),
        urgent=Count('id', filter=Q(priority='urgent')),
        high=Count('id', filter=Q(priority='high')),
        escalated=Count('id', filter=Q(is_escalated=True)),
    )

    # Tickets created today and this week
    tickets_today = tickets.filter(created_at__gte=today).count()
    tickets_this_week = tickets.filter(created_at__gte=last_7_days).count()

    # ── Trend Data (last 7 days) ──────────────────────────
    daily_created = []
    daily_resolved = []
    daily_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        daily_labels.append(day.strftime('%b %d'))
        daily_created.append(
            tickets.filter(created_at__gte=day, created_at__lt=next_day).count()
        )
        daily_resolved.append(
            tickets.filter(
                resolved_at__gte=day, resolved_at__lt=next_day
            ).count()
        )

    # ── Priority Distribution ─────────────────────────────
    priority_data = tickets.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')

    # ── Status Distribution ───────────────────────────────
    status_data = tickets.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    # ── Recent Tickets ────────────────────────────────────
    recent_tickets = tickets.select_related(
        'customer', 'assigned_agent', 'category'
    ).order_by('-created_at')[:10]

    # ── Agent Performance (staff only) ────────────────────
    agent_performance = []
    if user.is_staff_member:
        agents = User.objects.filter(
            role__in=['agent', 'manager', 'superadmin'],
            is_active=True,
        ).annotate(
            assigned_count=Count(
                'assigned_tickets',
                filter=Q(assigned_tickets__created_at__gte=last_30_days),
            ),
            resolved_count=Count(
                'assigned_tickets',
                filter=Q(
                    assigned_tickets__status__in=['resolved', 'closed'],
                    assigned_tickets__resolved_at__gte=last_30_days,
                ),
            ),
        ).order_by('-resolved_count')[:10]
        agent_performance = agents

    # ── SLA Stats (staff only) ────────────────────────────
    sla_stats = {}
    if user.is_staff_member:
        total_breaches = SLABreach.objects.count()
        recent_breaches = SLABreach.objects.filter(
            breached_at__gte=last_7_days
        ).count()
        sla_stats = {
            'total_breaches': total_breaches,
            'recent_breaches': recent_breaches,
        }

    # ── Customer-specific stats ───────────────────────────
    customer_stats = {}
    if user.is_customer:
        customer_stats = {
            'my_open': tickets.filter(status__in=['open', 'assigned', 'in_progress']).count(),
            'my_resolved': tickets.filter(status__in=['resolved', 'closed']).count(),
            'my_total': tickets.count(),
        }

    context = {
        'ticket_stats': ticket_stats,
        'tickets_today': tickets_today,
        'tickets_this_week': tickets_this_week,
        'daily_labels': daily_labels,
        'daily_created': daily_created,
        'daily_resolved': daily_resolved,
        'priority_data': list(priority_data),
        'status_data': list(status_data),
        'recent_tickets': recent_tickets,
        'agent_performance': agent_performance,
        'sla_stats': sla_stats,
        'customer_stats': customer_stats,
    }

    return render(request, 'dashboard/index.html', context)
