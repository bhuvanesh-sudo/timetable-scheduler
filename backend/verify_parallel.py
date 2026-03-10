import os
import sys

# Ensure backend directory is in sys.path
sys.path.append(os.getcwd())

def verify():
    # Force the correct settings module
    os.environ['DJANGO_SETTINGS_MODULE'] = 'timetable_project.settings'
    
    import django
    django.setup()
    
    from core.models import Schedule, ScheduleEntry, Course
    
    try:
        # Get the latest 'Final Parallel ODD 1M' schedule
        sched = Schedule.objects.filter(name='Final Parallel ODD 1M').latest('created_at')
        print(f"Schedule: {sched.name} ({sched.semester})")
        
        pe_ids = ['PE1', 'PE2', 'PE4', 'PE5', 'PE6', 'FREE2']
        
        print("\nGlobal Placement Stats:")
        for pid in pe_ids:
            course = Course.objects.filter(course_id=pid).first()
            if not course: continue
            entries = ScheduleEntry.objects.filter(schedule=sched, course=course)
            count = entries.count()
            secs = sorted(list(entries.values_list('section__class_id', flat=True).distinct()))
            print(f"  {pid}: {count} slots total. Sections: {secs}")

        # Check Day Coverage for a few more sections
        target_sections = ['CSE3A', 'CSE4A', 'CSE4G']
        for sec_id in target_sections:
            print(f"\nSection Details: {sec_id}")
            entries = ScheduleEntry.objects.filter(schedule=sched, section__class_id=sec_id).select_related('course', 'timeslot')
            
            all_days = set()
            for e in entries:
                all_days.add(e.timeslot.day)
            print(f"  Day Coverage: {sorted(list(all_days))}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
