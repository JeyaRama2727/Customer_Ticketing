"""
JeyaRamaDesk — Accounts API Serializers
"""

from rest_framework import serializers
from accounts.models import User, LoginAuditLog


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'department', 'job_title', 'is_active',
            'is_online', 'date_joined', 'last_login', 'avatar',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_online']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name',
            'role', 'phone', 'department', 'job_title',
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAuditLog
        fields = '__all__'
