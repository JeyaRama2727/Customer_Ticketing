"""
JeyaRamaDesk — SLA Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from sla.models import SLAPolicy, SLABreach
from sla.services.sla_service import SLAService


@login_required
def sla_list_view(request):
    """List SLA policies and breach dashboard."""
    if not request.user.is_staff_member:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:index')

    policies = SLAPolicy.objects.all()
    recent_breaches = SLABreach.objects.select_related('ticket', 'policy')[:20]
    stats = SLAService.get_sla_stats()

    return render(request, 'sla/sla_list.html', {
        'policies': policies,
        'breaches': recent_breaches,
        'stats': stats,
    })


@login_required
def sla_create_view(request):
    """Create a new SLA policy."""
    if request.user.role not in ('superadmin', 'manager'):
        messages.error(request, 'Permission denied.')
        return redirect('sla:list')

    if request.method == 'POST':
        SLAPolicy.objects.create(
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip(),
            priority=request.POST.get('priority', 'medium'),
            response_time_hours=int(request.POST.get('response_time_hours', 4)),
            resolution_time_hours=int(request.POST.get('resolution_time_hours', 24)),
            escalation_time_hours=int(request.POST.get('escalation_time_hours', 0)),
        )
        messages.success(request, 'SLA policy created.')
        return redirect('sla:list')

    return render(request, 'sla/sla_form.html', {'action': 'Create'})


@login_required
def sla_edit_view(request, pk):
    """Edit an SLA policy."""
    if request.user.role not in ('superadmin', 'manager'):
        messages.error(request, 'Permission denied.')
        return redirect('sla:list')

    policy = get_object_or_404(SLAPolicy, pk=pk)

    if request.method == 'POST':
        policy.name = request.POST.get('name', '').strip()
        policy.description = request.POST.get('description', '').strip()
        policy.priority = request.POST.get('priority', policy.priority)
        policy.response_time_hours = int(request.POST.get('response_time_hours', 4))
        policy.resolution_time_hours = int(request.POST.get('resolution_time_hours', 24))
        policy.escalation_time_hours = int(request.POST.get('escalation_time_hours', 0))
        policy.is_active = request.POST.get('is_active') == 'on'
        policy.save()
        messages.success(request, 'SLA policy updated.')
        return redirect('sla:list')

    return render(request, 'sla/sla_form.html', {'policy': policy, 'action': 'Edit'})
