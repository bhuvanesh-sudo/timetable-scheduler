"""
Unit Tests for Module 4 - Backend APIs

Tests REST endpoints, request validation, and serialization correctness.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Teacher, ChangeRequest

User = get_user_model()

@pytest.mark.django_db
class TestAPI:
    """Test cases for API endpoints and workflows"""

    @pytest.fixture
    def setup_users(self):
        admin = User.objects.create_user(username='admin_api', password='password123', role='ADMIN')
        hod = User.objects.create_user(username='hod_api', password='password123', role='HOD', department='CSE')
        return {'admin': admin, 'hod': hod}

    def test_teacher_list_success(self, setup_users):
        """Verify API returns valid JSON and status 200"""
        client = APIClient()
        client.force_authenticate(user=setup_users['hod'])
        
        response = client.get('/api/teachers/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_change_request_workflow(self, setup_users):
        """Verify full HOD request -> Admin approval -> DB update workflow (Module 4)"""
        client = APIClient()
        teacher = Teacher.objects.create(
            teacher_id='T501', teacher_name='Old Name', 
            email='old@mail.com', department='CSE', max_hours_per_week=10
        )
        
        # 1. HOD creates request
        client.force_authenticate(user=setup_users['hod'])
        req_data = {
            'target_model': 'Teacher', 'target_id': 'T501', 'change_type': 'UPDATE',
            'proposed_data': {'teacher_name': 'New Name API'}, 'request_notes': 'Update'
        }
        res = client.post('/api/change-requests/', req_data, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        req_id = res.data['id']
        
        # 2. Admin approves
        client.force_authenticate(user=setup_users['admin'])
        res = client.post(f'/api/change-requests/{req_id}/approve/', {'admin_notes': 'Ok'})
        assert res.status_code == status.HTTP_200_OK
        
        # 3. Verify Update
        teacher.refresh_from_db()
        assert teacher.teacher_name == 'New Name API'
