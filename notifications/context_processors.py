"""JeyaRamaDesk — Notification Context Processor"""

from notifications.models import Notification


def unread_notifications_count(request):
    """
    Inject ``unread_notifications_count`` into every template context
    so the topbar badge can be rendered without an extra query in every view.
    """
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count()
        }
    return {'unread_notifications_count': 0}
