"""JeyaRamaDesk — Notification Views"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """Display user's notifications with read/unread filter."""
    qs = Notification.objects.filter(user=request.user)

    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        qs = qs.filter(is_read=False)
    elif filter_type == 'read':
        qs = qs.filter(is_read=True)

    notifications = qs[:100]  # Latest 100
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'filter_type': filter_type,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_read(request, pk):
    """Mark a single notification as read (AJAX or form submit)."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_read()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_read(request):
    """Mark all of the user's unread notifications as read."""
    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect('notifications:list')


@login_required
def notification_open(request, pk):
    """Open a notification: mark it as read and redirect to the relevant page."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_read()
    if notification.ticket:
        return redirect('tickets:detail', ticket_id=notification.ticket.ticket_id)
    return redirect('notifications:list')


@login_required
def unread_count_api(request):
    """Quick JSON endpoint returning the unread count for the topbar badge."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})
