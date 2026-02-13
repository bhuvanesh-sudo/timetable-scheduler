
import os
import django
import sys
from django.core.management import call_command
from django.db.models import Count
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Course, Schedule, ScheduleEntry, ElectiveAssignment, Section
from scheduler.algorithm import generate_schedule
from rest_framework.test import APIClient

def verify():
    print("1. Verifying Import Logic...")
    sys.stdout.flush()
    # Import data
    call_command('import_data', clear=True)
    
    # Check electives count
    elective_count = Course.objects.filter(is_elective=True).count()
    total_count = Course.objects.count()
    print(f"   Total Courses: {total_count}")
    print(f"   Elective Courses Found: {elective_count}")
    
    if total_count < 165:
        print("   WARNING: Total count seems low if 165 were expected.")
    else:
        print("   Total count is >= 165. Correct.")
    sys.stdout.flush()

    print("\n2. Generating Schedule...")
    sys.stdout.flush()
    # Create schedule object
    schedule = Schedule.objects.create(
        name="Verification Schedule",
        semester="odd",
        year=1,
        status="PENDING"
    )
    
    success, message = generate_schedule(schedule.schedule_id)
    print(f"   Generation Result: {success} - {message}")
    sys.stdout.flush()
    
    if not success:
        print("   generation failed. Exiting.")
        return

    print("\n3. Verifying Start/End Day Constraints (No Empty Days)...")
    sys.stdout.flush()
    # Check for empty days for a few sections
    sections = Section.objects.all()[:5]
    for section in sections:
        # Check entries for this section
        entries = ScheduleEntry.objects.filter(schedule=schedule, section=section)
        days = set(entries.values_list('timeslot__day', flat=True))
        
        print(f"   Section {section.class_id}: {len(days)} days with classes {list(days)}")
        
        expected_days = {'MON', 'TUE', 'WED', 'THU', 'FRI'}
        missing = expected_days - days
        if missing:
             # Check if total hours are very low (e.g. < 5 hours)
             total_hours = entries.count()
             if total_hours < 5:
                 print(f"     (Low load: {total_hours} hours. Empty days might be unavoidable)")
             else:
                 print(f"     WARNING: Empty days detected: {missing}")
        else:
            print(f"     PASS: All days have classes.")
    sys.stdout.flush()

    print("\n4. Verifying Elective Assignments...")
    ea_count = ElectiveAssignment.objects.filter(schedule=schedule).count()
    print(f"   Elective Assignments created: {ea_count}")
    sys.stdout.flush()
    
    print("\n5. Verifying Conflicts API...")
    User = get_user_model()
    # Create admin user for API access
    # Use different username to avoid conflicts if possible
    user, created = User.objects.get_or_create(email='verifier@test.com', defaults={'first_name':'Verifier', 'last_name':'Bot'})
    if created:
        user.set_password('password')
        user.is_superuser = True
        user.is_staff = True
        user.save()
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    url = f'/api/scheduler/validate/{schedule.schedule_id}/'
    response = client.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Validation Status: {data.get('valid')}")
        print(f"   Conflicts Found: {len(data.get('conflicts', []))}")
        for c in data.get('conflicts', [])[:5]:
            print(f"   - {c}")
    else:
        print(f"   API Call Failed: {response.status_code} - {response.content}")
    sys.stdout.flush()

if __name__ == '__main__':
    verify()
