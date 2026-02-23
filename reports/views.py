"""\nJeyaRamaDesk — Reports Views\nGenerate and export comprehensive reports with filters.\nSupports CSV export and detailed analytics.\n"""

import csv
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Q, Avg, F
from django.utils import timezone

from tickets.models import Ticket, Category
from accounts.models import User
from sla.models import SLABreach


@login_required
def report_index_view(request):
    """Report selection and generation page."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    return render(request, 'reports/report_index.html')


@login_required
def ticket_summary_report(request):
    """Ticket summary report with date range and priority/status breakdown."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    now = timezone.now()
    date_from = request.GET.get('date_from', (now - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', now.strftime('%Y-%m-%d'))

    tickets = Ticket.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    summary = tickets.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        assigned=Count('id', filter=Q(status='assigned')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        resolved=Count('id', filter=Q(status='resolved')),
        closed=Count('id', filter=Q(status='closed')),
    )

    by_priority = tickets.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')

    by_category = tickets.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    by_source = tickets.values('source').annotate(
        count=Count('id')
    ).order_by('-count')

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ticket_summary_{date_from}_to_{date_to}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ticket ID', 'Title', 'Priority', 'Status', 'Category', 'Agent', 'Created', 'Resolved'])
        for t in tickets.select_related('category', 'assigned_agent').order_by('-created_at'):
            writer.writerow([
                t.ticket_id, t.title, t.priority, t.status,
                t.category.name if t.category else '',
                t.assigned_agent.full_name if t.assigned_agent else '',
                t.created_at.strftime('%Y-%m-%d %H:%M'),
                t.resolved_at.strftime('%Y-%m-%d %H:%M') if t.resolved_at else '',
            ])
        return response

    return render(request, 'reports/ticket_summary.html', {
        'summary': summary,
        'by_priority': list(by_priority),
        'by_category': list(by_category),
        'by_source': list(by_source),
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def agent_performance_report(request):
    """Agent performance report with resolution metrics."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    now = timezone.now()
    date_from = request.GET.get('date_from', (now - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', now.strftime('%Y-%m-%d'))

    agents = User.objects.filter(
        role__in=['agent', 'manager', 'superadmin'],
        is_active=True,
    ).annotate(
        total_assigned=Count(
            'assigned_tickets',
            filter=Q(
                assigned_tickets__created_at__date__gte=date_from,
                assigned_tickets__created_at__date__lte=date_to,
            ),
        ),
        total_resolved=Count(
            'assigned_tickets',
            filter=Q(
                assigned_tickets__status__in=['resolved', 'closed'],
                assigned_tickets__resolved_at__date__gte=date_from,
                assigned_tickets__resolved_at__date__lte=date_to,
            ),
        ),
        open_tickets=Count(
            'assigned_tickets',
            filter=Q(
                assigned_tickets__status__in=['open', 'assigned', 'in_progress'],
            ),
        ),
    ).order_by('-total_resolved')

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="agent_performance_{date_from}_to_{date_to}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Agent', 'Email', 'Role', 'Assigned', 'Resolved', 'Open', 'Resolution Rate'])
        for a in agents:
            rate = round((a.total_resolved / a.total_assigned * 100), 1) if a.total_assigned > 0 else 0
            writer.writerow([
                a.full_name, a.email, a.get_role_display(),
                a.total_assigned, a.total_resolved, a.open_tickets, f'{rate}%',
            ])
        return response

    return render(request, 'reports/agent_performance.html', {
        'agents': agents,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def sla_compliance_report(request):
    """SLA compliance report with breach details."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    now = timezone.now()
    date_from = request.GET.get('date_from', (now - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', now.strftime('%Y-%m-%d'))

    breaches = SLABreach.objects.filter(
        breached_at__date__gte=date_from,
        breached_at__date__lte=date_to,
    ).select_related('ticket', 'policy').order_by('-breached_at')

    total_tickets = Ticket.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    ).count()

    response_breaches = breaches.filter(breach_type='response').count()
    resolution_breaches = breaches.filter(breach_type='resolution').count()

    compliance_rate = 0
    if total_tickets > 0:
        unique_breached = breaches.values('ticket').distinct().count()
        compliance_rate = round(((total_tickets - unique_breached) / total_tickets) * 100, 1)

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sla_compliance_{date_from}_to_{date_to}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ticket ID', 'Ticket Title', 'Policy', 'Breach Type', 'Deadline', 'Breached At'])
        for b in breaches:
            writer.writerow([
                b.ticket.ticket_id, b.ticket.title, b.policy.name,
                b.breach_type, b.deadline.strftime('%Y-%m-%d %H:%M'),
                b.breached_at.strftime('%Y-%m-%d %H:%M'),
            ])
        return response

    return render(request, 'reports/sla_compliance.html', {
        'breaches': breaches,
        'total_tickets': total_tickets,
        'response_breaches': response_breaches,
        'resolution_breaches': resolution_breaches,
        'compliance_rate': compliance_rate,
        'date_from': date_from,
        'date_to': date_to,
    })
