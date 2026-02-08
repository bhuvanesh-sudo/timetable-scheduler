from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone']
        read_only_fields = ['role', 'department']  # Regular users can't change their role

class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for Admin to manage users"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone', 'is_active', 'is_protected']
        read_only_fields = ['is_protected'] # Protected status can only be set via database/superuser? Or Admin can set it? Let's generic admin set it? Maybe not.

