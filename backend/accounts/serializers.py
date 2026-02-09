from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    teacher_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone', 'teacher_id']
        read_only_fields = ['role', 'department']  # Regular users can't change their role
    
    def get_teacher_id(self, obj):
        if obj.role == 'FACULTY':
            from core.models import Teacher
            try:
                # Try finding teacher by email (most reliable)
                teacher = Teacher.objects.filter(email=obj.email).first()
                if teacher:
                    return teacher.teacher_id
                
                # Fallback: Try by username if username matches teacher_id pattern
                # or if username is the teacher_id
                teacher = Teacher.objects.filter(teacher_id=obj.username).first()
                if teacher:
                    return teacher.teacher_id
                    
            except Exception:
                pass
        return None

class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for Admin to manage users"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone', 'is_active', 'is_protected']
        read_only_fields = ['is_protected'] # Protected status can only be set via database/superuser? Or Admin can set it? Let's generic admin set it? Maybe not.

