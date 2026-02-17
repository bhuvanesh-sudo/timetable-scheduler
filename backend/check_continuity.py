import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, ScheduleEntry, Section, TimeSlot, Teacher

def check():
    s = Schedule.objects.latest('schedule_id')
    print(f"Checking continuity for Schedule: {s.name}")
    
    sections = Section.objects.all()
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    
    empty_secs = []
    for sec in sections:
        has_empty = False
        for d in days:
            if not ScheduleEntry.objects.filter(schedule=s, section=sec, timeslot__day=d).exists():
                print(f"  - Section {sec.class_id} has NO classes on {d}")
                has_empty = True
        if has_empty:
            empty_secs.append(sec.class_id)
            
    print(f"Total Sections with empty days: {len(empty_secs)}")
    
    # Check faculty Load < 40%
    teachers = Teacher.objects.all()
    underloaded = 0
    zero = 0
    for t in teachers:
        count = ScheduleEntry.objects.filter(schedule=s, teacher=t).count()
        util = (count / t.max_hours_per_week) * 100 if t.max_hours_per_week > 0 else 0
        if util == 0:
            zero += 1
        elif util < 40:
            underloaded += 1
            
    print(f"Teachers with 0 load: {zero}")
    print(f"Teachers with < 40% load: {underloaded}")

if __name__ == "__main__":
    check()
