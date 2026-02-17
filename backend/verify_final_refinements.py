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

def verify():
    print("--- Starting Final Verification ---")
    
    # Create a new schedule
    schedule = Schedule.objects.create(
        name=f"Final Refinement Test {int(time.time())}",
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
    
    # 1. Check Section Continuity
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    sections = Section.objects.all()
    sections_with_empty_days = 0
    
    for sec in sections:
        empty_days = []
        for d in days:
            if not ScheduleEntry.objects.filter(schedule=schedule, section=sec, timeslot__day=d).exists():
                empty_days.append(d)
        if empty_days:
            sections_with_empty_days += 1
            print(f"  [Continuity Issue] {sec.class_id} is empty on {empty_days}")
            
    if sections_with_empty_days == 0:
        print("SUCCESS: All sections have at least one class every day.")
    else:
        print(f"WARNING: {sections_with_empty_days} sections still have empty days.")

    # 2. Check Faculty Workload distribution
    teachers = Teacher.objects.all()
    under_40 = 0
    zero_load = 0
    for t in teachers:
        count = ScheduleEntry.objects.filter(schedule=schedule, teacher=t).count() + \
                ElectiveAssignment.objects.filter(schedule=schedule, teacher=t).count()
        util = (count / t.max_hours_per_week) * 100 if t.max_hours_per_week > 0 else 0
        
        if util == 0:
            zero_load += 1
        elif util < 40:
            under_40 += 1
            
    print(f"\nWorkload Distribution:")
    print(f"  Teachers with 0 load: {zero_load}")
    print(f"  Teachers < 40% load: {under_40}")

    # 3. Check Conflict Logs for Diagnostics
    print("\nDiagnostic Logs Generated:")
    diags = ConflictLog.objects.filter(schedule=schedule, conflict_type__in=['DATA_MAPPING_GAP', 'EMPTY_DAY_DETECTED', 'UNDERLOADED_FACULTY', 'CAPACITY_CRITICAL'])
    for c in diags:
        print(f"  [{c.severity}] {c.conflict_type}: {c.description[:150]}...")

if __name__ == "__main__":
    verify()
