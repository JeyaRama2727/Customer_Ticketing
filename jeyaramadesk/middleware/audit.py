"""
JeyaRamaDesk — Audit Middleware
Logs login events and tracks user activity.
"""

import logging
from django.utils import timezone

logger = logging.getLogger('jeyaramadesk')


class AuditMiddleware:
    """Middleware to log request metadata for audit trail."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Attach request metadata
        request.audit_ip = self._get_client_ip(request)
        request.audit_timestamp = timezone.now()

        response = self.get_response(request)

        # Log non-GET requests for authenticated users
        if request.method != 'GET' and hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(
                f'AUDIT | {request.method} {request.path} | '
                f'User: {request.user.email} | '
                f'IP: {request.audit_ip} | '
                f'Status: {response.status_code}'
            )

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
