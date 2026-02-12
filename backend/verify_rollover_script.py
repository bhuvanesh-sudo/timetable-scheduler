import os, sys, django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Schedule, TeacherCourseMapping, Section, Teacher, Course
from unittest.mock import patch

def verify():
    User = get_user_model()
    # Create admin
    admin, _ = User.objects.get_or_create(username='verifier', role='ADMIN')
    admin.set_password('pass')
    admin.save()

    client = APIClient()
    client.force_authenticate(user=admin)

    # Clean existing data to avoid conflicts
    TeacherCourseMapping.objects.all().delete()
    Schedule.objects.all().delete()
    Teacher.objects.filter(teacher_id='V_T1').delete()
    Course.objects.filter(course_id='V_C1').delete()
    Section.objects.filter(class_id='V_S1').delete()

    # Create dummy data
    t = Teacher.objects.create(teacher_id='V_T1', teacher_name='Verifier', email='v@t.com', department='CSE', max_hours_per_week=10)
    c = Course.objects.create(course_id='V_C1', course_name='Verify', year=1, semester='odd', lectures=1, theory=1, practicals=0, credits=1, weekly_slots=1)
    s = Section.objects.create(class_id='V_S1', year=1, section='V', department='CSE')
    
    # These should be deleted
    TeacherCourseMapping.objects.create(teacher=t, course=c)
    Schedule.objects.create(name="Verify Schedule", semester='odd', year=1)

    print(f"Pre-reset: Sched={Schedule.objects.count()}, Map={TeacherCourseMapping.objects.count()}, Sect={Section.objects.count()}")

    # Patch backup to avoid command failure
    with patch('core.system_views._create_db_backup') as mock_backup:
        mock_backup.return_value = {'filename': 'mock.sqlite3', 'size_display': '0B'}
        
        # Execute
        print("Executing reset-semester...")
        resp = client.post('/api/system/reset-semester/', {'confirmation': 'CONFIRM'}, format='json')
        print(f"Response Status: {resp.status_code}")
        content = resp.content.decode('utf-8')
        if content.strip().startswith('<!DOCTYPE') or '<html' in content:
             print("Response Content: HTML Document (Login page or Error page)")
             print(f"Title: {content.split('title>')[1].split('</')[0] if 'title>' in content else 'No Title'}")
        else:
             print(f"Response Content: {content[:500]}") # Truncate if long
        
        # Only try to access data if it's a DRF response
        if getattr(resp, 'data', None):
             print(f"Response Data: {resp.data}")

    sched_count = Schedule.objects.count()
    map_count = TeacherCourseMapping.objects.count()
    sect_count = Section.objects.count()
    
    print(f"Post-reset: Sched={sched_count}, Map={map_count}, Sect={sect_count}")
    
    if sched_count == 0 and map_count == 0 and sect_count >= 1:
        print("SUCCESS: Operations data cleared, Master data preserved.")
    else:
        print("FAILURE: Validation logic failed.")

if __name__ == "__main__":
    verify()
