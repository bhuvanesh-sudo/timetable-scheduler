import os
import django
import sys
import time

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, Teacher, ScheduleEntry, ElectiveAssignment, ConflictLog, Section
from scheduler.algorithm import generate_schedule

def verify_absolute():
    print("--- Starting Absolute Continuity Verification ---")
    
    # Create a new schedule
    schedule = Schedule.objects.create(
        name=f"Absolute Continuity Test {int(time.time())}",
        semester='even',
        year=2026,
        status='PENDING'
    )
    
    print(f"Generating Schedule ID: {schedule.schedule_id}...")
    success, message = generate_schedule(schedule.schedule_id)
    
    if not success:
        print(f"FAILED: {message}")
        return

    print(f"SUCCESS: {message}")
    
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    
    # 1. Check Section Continuity (No Empty Days)
    sections = Section.objects.all()
    sec_empty_count = 0
    for sec in sections:
        empty_days = []
        for d in days:
            if not ScheduleEntry.objects.filter(schedule=schedule, section=sec, timeslot__day=d).exists():
                empty_days.append(d)
        if empty_days:
            sec_empty_count += len(empty_days)
            print(f"  [Section Gap] {sec.class_id} empty on {empty_days}")
    
    # 2. Check Faculty Continuity (No Empty Days)
    teachers = Teacher.objects.all()
    teacher_empty_count = 0
    under_40_count = 0
    zero_count = 0
    
    for t in teachers:
        # Check load
        c_count = ScheduleEntry.objects.filter(schedule=schedule, teacher=t).count()
        e_count = ElectiveAssignment.objects.filter(schedule=schedule, teacher=t).count()
        total = c_count + e_count
        util = (total / t.max_hours_per_week) * 100 if t.max_hours_per_week > 0 else 0
        
        if util == 0: zero_count += 1
        elif util < 40: under_40_count += 1
        
        # Check presence
        empty_days = []
        for d in days:
            has_core = ScheduleEntry.objects.filter(schedule=schedule, teacher=t, timeslot__day=d).exists()
            has_elec = ElectiveAssignment.objects.filter(schedule=schedule, teacher=t, timeslot__day=d).exists()
            if not (has_core or has_elec):
                empty_days.append(d)
        if empty_days:
            teacher_empty_count += 1
            # print(f"  [Teacher Gap] {t.teacher_name} empty on {empty_days}")
            
    print(f"\nFinal Audit Results:")
    print(f"  Total Section-Day Gaps: {sec_empty_count}")
    print(f"  Teachers with Empty Days: {teacher_empty_count}/{teachers.count()}")
    print(f"  Teachers with 0% Load: {zero_count}")
    print(f"  Teachers with < 40% Load: {under_40_count}")
    
    if sec_empty_count == 0 and teacher_empty_count == 0:
        print("\nPASSED: Absolute continuity achieved for all!")
    else:
        print("\nWARNING: Continuity gaps remain.")

if __name__ == "__main__":
    verify_absolute()
