
import os
import django
import sys

# Setup Django environment
sys.path.append('/Users/Vamsi/Desktop/SE/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import (
    Schedule, ScheduleEntry, ConflictLog,
    TeacherCourseMapping, Section, Course, Teacher, Room,
    AuditLog, ChangeRequest
)

def reset_system():
    print("WARNING: This will delete all operational data!")
    confirm = "yes" # input("Type 'yes' to confirm: ")
    if confirm != 'yes':
        print("Aborted.")
        return

    print("Deleting Schedules...")
    Schedule.objects.all().delete()
    
    print("Deleting Mappings...")
    TeacherCourseMapping.objects.all().delete()
    
    print("Deleting Sections...")
    Section.objects.all().delete()
    
    print("Deleting Courses...")
    Course.objects.all().delete()
    
    print("Deleting Teachers...")
    Teacher.objects.all().delete()
    
    print("Deleting Rooms...")
    Room.objects.all().delete()
    
    print("Deleting Audit Logs & Requests...")
    AuditLog.objects.all().delete()
    ChangeRequest.objects.all().delete()
    
    print("System Reset Complete. Users and TimeSlots preserved.")

if __name__ == '__main__':
    reset_system()
