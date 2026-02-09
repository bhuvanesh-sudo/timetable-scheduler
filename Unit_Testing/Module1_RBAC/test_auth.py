"""
Unit Tests for Module 1 - Authentication & RBAC

Tests the security, permissions, and role-based access control.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Teacher, ChangeRequest

User = get_user_model()

@pytest.mark.django_db
class TestRBAC:
    """Test cases for permissions and role isolation"""

    @pytest.fixture
    def setup_users(self):
        admin = User.objects.create_user(
            username='admin_user', password='password123', role='ADMIN'
        )
        hod = User.objects.create_user(
            username='hod_user', password='password123', role='HOD', department='CSE'
        )
        faculty = User.objects.create_user(
            username='faculty_user', password='password123', role='FACULTY', department='CSE'
        )
        return {'admin': admin, 'hod': hod, 'faculty': faculty}

    def test_teacher_create_permissions(self, setup_users):
        """Verify only Admin/HOD can create teachers (Module 1 feature)"""
        client = APIClient()
        teacher_data = {
            'teacher_id': 'T999', 'teacher_name': 'New Prof',
            'email': 'new@mail.com', 'department': 'CSE', 'max_hours_per_week': 15
        }

        # 1. Faculty - Should FAIL (403 Forbidden)
        client.force_authenticate(user=setup_users['faculty'])
        response = client.post('/api/teachers/', teacher_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # 2. HOD - Should SUCCEED (201 Created)
        client.force_authenticate(user=setup_users['hod'])
        response = client.post('/api/teachers/', teacher_data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_audit_log_isolation(self, setup_users):
        """Verify Faculty cannot access audit logs (Module 1 feature)"""
        client = APIClient()
        client.force_authenticate(user=setup_users['faculty'])
        
        response = client.get('/api/audit-logs/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_request_hod_isolation(self, setup_users):
        """Verify HODs only see their OWN change requests (Module 1 feature)"""
        hod2 = User.objects.create_user(
            username='hod_other', password='password123', role='HOD', department='ECE'
        )
        
        ChangeRequest.objects.create(
            requested_by=setup_users['hod'],
            target_model='Teacher',
            change_type='CREATE',
            proposed_data={'name': 'HOD1 Request'}
        )
        
        ChangeRequest.objects.create(
            requested_by=hod2,
            target_model='Teacher',
            change_type='CREATE',
            proposed_data={'name': 'HOD2 Request'}
        )
        
        client = APIClient()
        client.force_authenticate(user=setup_users['hod'])
        response = client.get('/api/change-requests/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['requested_by'] == setup_users['hod'].id
