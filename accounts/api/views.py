"""
JeyaRamaDesk — Accounts API Views
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.models import User
from accounts.permissions import IsSuperAdmin, IsManager
from accounts.api.serializers import UserSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for user management."""

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'role']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current authenticated user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def agents(self, request):
        """List all active agents."""
        agents = User.objects.filter(
            role__in=['agent', 'manager', 'superadmin'],
            is_active=True,
        )
        serializer = UserSerializer(agents, many=True)
        return Response(serializer.data)
