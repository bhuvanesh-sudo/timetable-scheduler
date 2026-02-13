
import os
import django
import sys
from django.db.models import Count
from django.contrib.auth import get_user_model # Added for user model access
from django.apps import apps
# APIClient import moved to after setup

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Course, Section, Room, TimeSlot, Teacher, Schedule, ScheduleEntry
# ConflictLog import removed to avoid ImportError if it's not loaded yet
from scheduler.constraints import ConstraintValidator
from rest_framework.test import APIClient

def diagnose():
    print("Diagnosis Started...")
    
    # Create admin user for API access
    User = get_user_model()
    user, created = User.objects.get_or_create(email='verifier@test.com', defaults={'first_name':'Verifier', 'last_name':'Bot', 'role':'ADMIN'})
    if created:
        user.set_password('password')
        user.is_superuser = True
        user.is_staff = True
        user.save()
    elif user.role != 'ADMIN':
        user.role = 'ADMIN'
        user.save()
    
    # 1. Schedulable Courses
    db_courses = Course.objects.filter(is_schedulable=True)
    print(f"Schedulable Courses: {db_courses.count()}")
    if db_courses.count() == 0:
        print("CRITICAL: No courses are marked schedulable!")
        
    # 2. Check Assignments
    # We don't have direct assignment model, it's a JSON field or implied?
    # Teacher mappings are in Course -> Teacher?
    # No, Mappings are creating `TeacherAssignment`? 
    # Wait, `algorithm.py` uses `self.teacher_assignments`. 
    # Where does it get them? 
    # `self.teacher_assignments = self._get_teacher_assignments()`
    # It reads from `db`.
    # Let's check `import_data.py` - it populates `TeacherCourseMapping`?
    # No, it might be using `Course.teacher`?
    # Let's check `core/models.py`.
    
    # 3. Check Rooms
    rooms = Room.objects.all()
    print(f"Rooms: {rooms.count()}")
    print(f"Classrooms: {rooms.filter(room_type='CLASSROOM').count()}")
    print(f"Lab Rooms: {rooms.filter(room_type='LAB').count()}")
    
    # 4. Check ConflictLog
    print("\nConflict Log (Last 20):")
    try:
        ConflictLog = apps.get_model('core', 'ConflictLog')
        logs = ConflictLog.objects.all().order_by('-detected_at')[:20]
        for log in logs:
            print(f"{log.conflict_type}: {log.description}")
    except Exception as e:
        print(f"Could not load ConflictLog: {e}")
        
    # 5. Manual Constraint Check
    print("\nManual Constraint Check:")
    schedule = Schedule.objects.last()
    if not schedule: return
    
    validator = ConstraintValidator(schedule)
    
    # Pick a course
    course = db_courses.first()
    if not course: return
    
    section = Section.objects.first()
    teacher = Teacher.objects.first() 
    room = rooms.first()
    timeslot = TimeSlot.objects.first()
    
    print(f"Testing validation for: {course.course_id}, {section.class_id}, {teacher.teacher_name}, {room.room_id}, {timeslot}")
    
    is_valid, reason = validator.validate_all(section, course, teacher, room, timeslot)
    print(f"Result: {is_valid}, Reason: {reason}")
    
    if not is_valid:
        print("Detailed Checks:")
        print(f"  Teacher Avail: {validator.validate_teacher_availability(teacher, timeslot)}")
        print(f"  Room Avail: {validator.validate_room_availability(room, timeslot)}")
        print(f"  Section Avail: {validator.validate_section_availability(section, timeslot)}")
        print(f"  Room Type: {validator.validate_room_type(room, course)}")

if __name__ == '__main__':
    diagnose()
