"""
JeyaRamaDesk — Knowledge Base API Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q

from accounts.permissions import IsStaffMember
from knowledge_base.models import KBCategory, Article
from .serializers import KBCategorySerializer, ArticleListSerializer, ArticleDetailSerializer


class KBCategoryViewSet(viewsets.ModelViewSet):
    """API for KB categories. Public read, staff write."""
    queryset = KBCategory.objects.filter(is_active=True).order_by('order')
    serializer_class = KBCategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsStaffMember()]


class ArticleViewSet(viewsets.ModelViewSet):
    """API for KB articles. Public read for published, staff write."""
    serializer_class = ArticleListSerializer

    def get_queryset(self):
        qs = Article.objects.select_related('category', 'author')
        if self.request.user.is_authenticated and hasattr(self.request.user, 'is_staff_member') and self.request.user.is_staff_member:
            return qs.order_by('-updated_at')
        return qs.filter(status='published', is_internal=False).order_by('-published_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        return ArticleListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsStaffMember()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search articles by query string."""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])

        qs = Article.objects.filter(
            Q(title__icontains=query) | Q(body__icontains=query),
            status='published',
        )
        if not request.user.is_authenticated:
            qs = qs.filter(is_internal=False)

        serializer = ArticleListSerializer(qs[:20], many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """Submit helpfulness feedback."""
        article = self.get_object()
        feedback_type = request.data.get('feedback')
        from django.db.models import F
        if feedback_type == 'yes':
            Article.objects.filter(pk=article.pk).update(helpful_yes=F('helpful_yes') + 1)
        elif feedback_type == 'no':
            Article.objects.filter(pk=article.pk).update(helpful_no=F('helpful_no') + 1)
        return Response({'success': True})
