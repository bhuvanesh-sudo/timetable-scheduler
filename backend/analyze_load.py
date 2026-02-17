import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, Teacher, ScheduleEntry, ElectiveAssignment

def analyze_load(schedule_id=None):
    if not schedule_id:
        schedule = Schedule.objects.filter(status='COMPLETED').first()
        if not schedule:
            print("No completed schedule found.")
            return
        schedule_id = schedule.schedule_id
    else:
        schedule = Schedule.objects.get(schedule_id=schedule_id)

    print(f"--- Analyzing Load for Schedule: {schedule.name} ({schedule_id}) ---")
    
    teachers = Teacher.objects.all()
    results = []
    
    for t in teachers:
        core_load = ScheduleEntry.objects.filter(schedule_id=schedule_id, teacher=t).count()
        elective_load = ElectiveAssignment.objects.filter(schedule_id=schedule_id, teacher=t).count()
        total_load = core_load + elective_load
        utilization = (total_load / t.max_hours_per_week) * 100 if t.max_hours_per_week > 0 else 0
        
        results.append({
            'name': t.teacher_name,
            'total': total_load,
            'max': t.max_hours_per_week,
            'util': utilization
        })
    
    # Sort by utilization
    results.sort(key=lambda x: x['util'])
    
    print("\nFaculty with LOWEST utilization:")
    for r in results[:15]:
        print(f"{r['name']}: {r['util']:.2f}% ({r['total']}/{r['max']}h)")
        
    print("\nFaculty with HIGHEST utilization:")
    for r in results[-15:]:
        print(f"{r['name']}: {r['util']:.2f}% ({r['total']}/{r['max']}h)")

    under_50 = [r for r in results if r['util'] < 50]
    zero_load = [r for r in results if r['total'] == 0]
    
    print(f"\nSummary:")
    print(f"Teachers < 50% load: {len(under_50)}")
    print(f"Teachers with 0 load: {len(zero_load)}")

if __name__ == "__main__":
    analyze_load()
