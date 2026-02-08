import os
import django
import random
from datetime import time

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Teacher, Course, Room, TimeSlot, Section, TeacherCourseMapping

User = get_user_model()

def run():
    print("⚠️  Clearing existing data...")
    # Order matters due to foreign keys
    TeacherCourseMapping.objects.all().delete()
    Section.objects.all().delete()
    Room.objects.all().delete()
    Course.objects.all().delete()
    Teacher.objects.all().delete()
    TimeSlot.objects.all().delete()
    User.objects.all().delete()
    
    print("👤 Creating Users...")
    # Admin
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print(" - Created Superuser: admin/admin")
    
    # HOD CSE
    hod_cse = User.objects.create_user('hod_cse', 'hod@cse.com', 'password123', role='HOD', department='CSE')
    print(" - Created HOD: hod_cse/password123")
    
    # Faculty CSE
    fac1 = User.objects.create_user('teacher_cse_1', 't1@cse.com', 'password123', role='FACULTY', department='CSE')
    print(" - Created Faculty: teacher_cse_1/password123")
    
    fac2 = User.objects.create_user('teacher_cse_2', 't2@cse.com', 'password123', role='FACULTY', department='CSE')
    print(" - Created Faculty: teacher_cse_2/password123")
    
    print("🏫 Creating Core Data...")
    
    # Teachers
    # Note: teacher_id T001 matches teacher_cse_1's intended identity
    t1 = Teacher.objects.create(teacher_id='T001', teacher_name='teacher_cse_1', email='t1@cse.com', department='CSE', max_hours_per_week=20)
    t2 = Teacher.objects.create(teacher_id='T002', teacher_name='teacher_cse_2', email='t2@cse.com', department='CSE', max_hours_per_week=20)
    
    # Courses
    c1 = Course.objects.create(
        course_id='CSE101', 
        course_name='Introduction to Computer Science', 
        year=1, 
        semester='odd', 
        lectures=3, 
        theory=3, 
        practicals=0, 
        credits=3, 
        weekly_slots=3
    )
    c2 = Course.objects.create(
        course_id='CSE201', 
        course_name='Data Structures', 
        year=2, 
        semester='odd', 
        lectures=3, 
        theory=3, 
        practicals=2, 
        credits=4, 
        weekly_slots=5, 
        is_lab=True
    )
    
    # Rooms
    Room.objects.create(room_id='CR-101', block='A', floor=1, room_type='CLASSROOM')
    Room.objects.create(room_id='LAB-101', block='B', floor=1, room_type='LAB')
    
    # Sections
    Section.objects.create(class_id='CSE-1A', year=1, section='A', department='CSE')
    Section.objects.create(class_id='CSE-2A', year=2, section='A', department='CSE')
    
    # Teacher Mappings
    TeacherCourseMapping.objects.create(teacher=t1, course=c1, preference_level=5)
    TeacherCourseMapping.objects.create(teacher=t2, course=c2, preference_level=4)
    
    print("✅ Data populated successfully!")

if __name__ == '__main__':
    run()
