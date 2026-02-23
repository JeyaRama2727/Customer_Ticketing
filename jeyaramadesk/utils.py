"""
JeyaRamaDesk — Shared Utilities
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('jeyaramadesk')


def custom_exception_handler(exc, context):
    """Enhanced DRF exception handler with logging."""
    response = exception_handler(exc, context)

    if response is None:
        logger.error(f'Unhandled exception: {exc}', exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Standardize error format
    if isinstance(response.data, dict):
        response.data = {
            'error': True,
            'status_code': response.status_code,
            'details': response.data,
        }

    return response
