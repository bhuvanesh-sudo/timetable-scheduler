
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, ScheduleEntry, Teacher, Section, Course

def check():
    dept = 'CSE'
    print(f"--- Department: {dept} ---")
    print(f"Total Teachers in {dept}: {Teacher.objects.filter(department=dept).count()}")
    print(f"Total Sections in {dept}: {Section.objects.filter(department=dept).count()}")
    print(f"Total Courses: {Course.objects.count()}")
    print(f"Courses with NO department: {Course.objects.filter(department='').count()}")
    print(f"Unique Departments in Courses: {list(Course.objects.values_list('department', flat=True).distinct())}")
    
    # List some courses
    print("\n--- Example Courses ---")
    for c in Course.objects.all()[:5]:
        print(f"Course: {c.course_id}, Name: {c.course_name}, Dept: '{c.department}'")
    schedules = Schedule.objects.all()
    for s in schedules:
        print(f"Schedule ID: {s.schedule_id}, Status: {s.status}, Entries: {ScheduleEntry.objects.filter(schedule=s).count()}")
    
    # Check specific teachers from user screenshot
    target_names = ['Aarthi R', 'Abirami K', 'Anantha Narayanan V']
    print("\n--- Checking Target Teachers (from Screenshot) ---")
    for name in target_names:
        try:
            t = Teacher.objects.get(teacher_name=name)
            load = ScheduleEntry.objects.filter(teacher=t, schedule__status='COMPLETED').count()
            print(f"Name: {name}, Load (COMPLETED): {load}")
        except Teacher.DoesNotExist:
            print(f"Name: {name} not found in DB")

    # List teachers that DO have load
    print("\n--- Top 10 Teachers with Load > 0 ---")
    teachers_with_load = Teacher.objects.filter(
        department=dept,
        scheduleentry__schedule__status='COMPLETED'
    ).distinct()[:10]
    for t in teachers_with_load:
        load = ScheduleEntry.objects.filter(teacher=t, schedule__status='COMPLETED').count()
        print(f"Teacher: {t.teacher_name}, Load: {load}")

if __name__ == "__main__":
    check()
