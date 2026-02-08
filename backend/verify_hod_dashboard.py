import os
import django
import sys
import json

# Setup Django environment
sys.path.append('e:/sem 6/akshi_seproj/timetable-scheduler/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Teacher, Section
from rest_framework.test import APIRequestFactory, force_authenticate
from core.views import DashboardStatsView

User = get_user_model()

def verify_hod_dashboard():
    print("Verifying HOD Dashboard API...")

    # 1. Create Test HOD User
    username = 'test_hod'
    password = 'test_password'
    email = 'hod@test.com'
    dept = 'CSE'
    
    user, created = User.objects.get_or_create(username=username, email=email)
    user.set_password(password)
    user.role = 'HOD'
    user.department = dept
    user.save()
    print(f"Created HOD user: {username} ({dept})")

    # 2. Create Test Data
    # Create teachers in CSE
    t1, _ = Teacher.objects.get_or_create(teacher_id='T_CSE_01', teacher_name='CSE Prof 1', department=dept, max_hours_per_week=10)
    t2, _ = Teacher.objects.get_or_create(teacher_id='T_CSE_02', teacher_name='CSE Prof 2', department=dept, max_hours_per_week=12)
    # Create teacher in ECE
    t3, _ = Teacher.objects.get_or_create(teacher_id='T_ECE_01', teacher_name='ECE Prof 1', department='ECE', max_hours_per_week=10)
    
    # Create sections in CSE
    s1, _ = Section.objects.get_or_create(class_id='CSE_3A', year=3, section='A', sem='odd', department=dept)
    
    print("Created test data: 2 CSE teachers, 1 ECE teacher, 1 CSE section")

    # 3. Test API
    factory = APIRequestFactory()
    view = DashboardStatsView.as_view()
    
    request = factory.get('/api/dashboard-stats/')
    force_authenticate(request, user=user)
    
    response = view(request)
    
    print(f"API Response Status: {response.status_code}")
    data = response.data
    
    # 4. Assertions
    if 'department_stats' not in data:
        print("FAIL: 'department_stats' missing in response")
        return

    dept_stats = data['department_stats']
    
    if dept_stats['department'] != dept:
        print(f"FAIL: Expected department {dept}, got {dept_stats['department']}")
    
    # Check if we have at least the ones we created
    # We can't know exact number if DB is pre-populated
    
    cse_teachers_count = Teacher.objects.filter(department='CSE').count()
    if dept_stats['total_faculty'] != cse_teachers_count:
         print(f"FAIL: Expected {cse_teachers_count} faculty (actual DB count), got {dept_stats['total_faculty']} (API count)")
    else:
         print(f"SUCCESS: HOD Dashboard API verified! Found {dept_stats['total_faculty']} faculty in {dept} (Matches DB)")

    # Cleanup (Optional, but good practice for repeatable tests)
    # User.objects.filter(username=username).delete()
    # Teacher.objects.filter(teacher_id__in=['T_CSE_01', 'T_CSE_02', 'T_ECE_01']).delete()
    # Section.objects.filter(class_id='CSE_3A').delete()

if __name__ == "__main__":
    verify_hod_dashboard()
