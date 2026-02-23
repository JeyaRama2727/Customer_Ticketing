"""
JeyaRamaDesk — Ticket API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, CategoryViewSet, TagViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
