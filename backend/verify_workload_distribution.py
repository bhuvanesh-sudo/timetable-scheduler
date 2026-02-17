import os
import django
import sys
import time

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, Teacher, ScheduleEntry, ElectiveAssignment, ConflictLog
from scheduler.algorithm import generate_schedule

def verify_balancing():
    print("--- Starting Workload Balancing Verification ---")
    
    # Create a new schedule for testing
    schedule = Schedule.objects.create(
        name=f"Balancing Test {int(time.time())}",
        semester='even',
        year=2026,
        status='PENDING'
    )
    
    print(f"Triggering generation for Schedule ID: {schedule.schedule_id}...")
    success, message = generate_schedule(schedule.schedule_id)
    
    if not success:
        print(f"FAILED: Generation failed with message: {message}")
        return

    print(f"SUCCESS: {message}")
    
    # Analyze load using logic from analyze_load.py
    teachers = Teacher.objects.all()
    results = []
    
    for t in teachers:
        core_count = ScheduleEntry.objects.filter(schedule=schedule, teacher=t).count()
        elective_count = ElectiveAssignment.objects.filter(schedule=schedule, teacher=t).count()
        total_load = core_count + elective_count
        utilization = (total_load / t.max_hours_per_week) * 100 if t.max_hours_per_week > 0 else 0
        
        results.append({
            'name': t.teacher_name,
            'total': total_load,
            'max': t.max_hours_per_week,
            'util': utilization
        })
    
    results.sort(key=lambda x: x['util'])
    
    zero_load = [r for r in results if r['total'] == 0]
    under_50 = [r for r in results if r['util'] < 50]
    over_95 = [r for r in results if r['util'] > 95]
    
    print(f"\nWorkload Distribution Results:")
    print(f"Total Teachers: {len(results)}")
    print(f"Teachers with 0 load: {len(zero_load)}")
    print(f"Teachers < 50% load: {len(under_50)}")
    print(f"Teachers > 95% load: {len(over_95)}")
    
    print("\nSample - Lowest Utilized:")
    for r in results[:10]:
        print(f"  {r['name']}: {r['util']:.2f}% ({r['total']}/{r['max']}h)")
        
    print("\nConflicts Logged:")
    conflicts = ConflictLog.objects.filter(schedule=schedule, conflict_type__in=['UNDERLOADED_FACULTY', 'CAPACITY_CRITICAL', 'OVERLOAD_PREVENTED'])
    for c in conflicts:
        print(f"  [{c.severity}] {c.conflict_type}: {c.description[:120]}...")

if __name__ == "__main__":
    verify_balancing()
