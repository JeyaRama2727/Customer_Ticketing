"""
JeyaRamaDesk — Rate Limiting Middleware
Simple in-memory rate limiter for critical endpoints.
"""

import time
import logging
from collections import defaultdict
from django.http import JsonResponse

logger = logging.getLogger('jeyaramadesk')

# In-memory store: IP -> list of request timestamps
_rate_store = defaultdict(list)

# Configuration
RATE_LIMIT_PATHS = ['/accounts/login/', '/api/token/']
MAX_REQUESTS = 10
WINDOW_SECONDS = 60


class RateLimitMiddleware:
    """Simple per-IP rate limiter for auth endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in RATE_LIMIT_PATHS):
            ip = self._get_ip(request)
            now = time.time()

            # Clean old entries
            _rate_store[ip] = [
                t for t in _rate_store[ip] if now - t < WINDOW_SECONDS
            ]

            if len(_rate_store[ip]) >= MAX_REQUESTS:
                logger.warning(f'Rate limit exceeded for IP: {ip} on {request.path}')
                return JsonResponse(
                    {'error': 'Too many requests. Please try again later.'},
                    status=429,
                )

            _rate_store[ip].append(now)

        return self.get_response(request)

    @staticmethod
    def _get_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
