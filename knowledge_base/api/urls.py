"""
JeyaRamaDesk — Knowledge Base API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.KBCategoryViewSet, basename='kb-category')
router.register(r'articles', views.ArticleViewSet, basename='kb-article')

urlpatterns = [
    path('', include(router.urls)),
]
