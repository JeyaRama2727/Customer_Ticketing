"""
JeyaRamaDesk — Automation Views
Template views for managing automation rules.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import AutomationRule, AutomationLog
from .services.automation_service import AutomationService


@login_required
def rule_list_view(request):
    """Display all automation rules with stats and recent logs."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    rules = AutomationRule.objects.all().order_by('priority_order', '-created_at')
    recent_logs = AutomationLog.objects.select_related(
        'rule', 'ticket'
    ).order_by('-executed_at')[:20]
    stats = AutomationService.get_rule_stats()

    return render(request, 'automation/rule_list.html', {
        'rules': rules,
        'recent_logs': recent_logs,
        'stats': stats,
    })


@login_required
def rule_create_view(request):
    """Create a new automation rule."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        try:
            conditions_str = request.POST.get('conditions', '{}')
            action_params_str = request.POST.get('action_params', '{}')

            conditions = json.loads(conditions_str) if conditions_str else {}
            action_params = json.loads(action_params_str) if action_params_str else {}

            rule = AutomationRule.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                trigger_event=request.POST.get('trigger_event'),
                conditions=conditions,
                action_type=request.POST.get('action_type'),
                action_params=action_params,
                priority_order=int(request.POST.get('priority_order', 0)),
                is_active=request.POST.get('is_active') == 'on',
                stop_processing=request.POST.get('stop_processing') == 'on',
                created_by=request.user,
            )
            messages.success(request, f'Rule "{rule.name}" created successfully.')
            return redirect('automation:list')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON in conditions or action parameters.')
        except Exception as e:
            messages.error(request, f'Error creating rule: {e}')

    return render(request, 'automation/rule_form.html', {
        'trigger_choices': AutomationRule.TriggerEvent.choices,
        'action_choices': AutomationRule.ActionType.choices,
    })


@login_required
def rule_edit_view(request, pk):
    """Edit an existing automation rule."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    rule = get_object_or_404(AutomationRule, pk=pk)

    if request.method == 'POST':
        try:
            conditions_str = request.POST.get('conditions', '{}')
            action_params_str = request.POST.get('action_params', '{}')

            rule.name = request.POST.get('name')
            rule.description = request.POST.get('description', '')
            rule.trigger_event = request.POST.get('trigger_event')
            rule.conditions = json.loads(conditions_str) if conditions_str else {}
            rule.action_type = request.POST.get('action_type')
            rule.action_params = json.loads(action_params_str) if action_params_str else {}
            rule.priority_order = int(request.POST.get('priority_order', 0))
            rule.is_active = request.POST.get('is_active') == 'on'
            rule.stop_processing = request.POST.get('stop_processing') == 'on'
            rule.save()

            messages.success(request, f'Rule "{rule.name}" updated successfully.')
            return redirect('automation:list')
        except json.JSONDecodeError:
            messages.error(request, 'Invalid JSON in conditions or action parameters.')
        except Exception as e:
            messages.error(request, f'Error updating rule: {e}')

    return render(request, 'automation/rule_form.html', {
        'rule': rule,
        'trigger_choices': AutomationRule.TriggerEvent.choices,
        'action_choices': AutomationRule.ActionType.choices,
    })


@login_required
def rule_delete_view(request, pk):
    """Delete an automation rule."""
    if not request.user.is_superadmin:
        messages.error(request, 'Only super admins can delete automation rules.')
        return redirect('automation:list')

    rule = get_object_or_404(AutomationRule, pk=pk)

    if request.method == 'POST':
        name = rule.name
        rule.delete()
        messages.success(request, f'Rule "{name}" deleted.')
        return redirect('automation:list')

    return render(request, 'automation/rule_confirm_delete.html', {'rule': rule})


@login_required
def rule_logs_view(request):
    """View automation execution logs."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    logs = AutomationLog.objects.select_related(
        'rule', 'ticket'
    ).order_by('-executed_at')

    status_filter = request.GET.get('status')
    if status_filter:
        logs = logs.filter(status=status_filter)

    paginator = Paginator(logs, 25)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    return render(request, 'automation/rule_logs.html', {
        'logs': logs_page,
        'status_filter': status_filter,
    })
