
import os
import django
import sys
from django.db.models import Count
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, ScheduleEntry, ElectiveAssignment, Section
from rest_framework.test import APIClient

def verify_results():
    schedule = Schedule.objects.last()
    if not schedule:
        print("No schedule found!")
        return
        
    print(f"Checking Schedule: {schedule.name} (ID: {schedule.schedule_id})")
    print(f"Status: {schedule.status}")

    print("\n1. Verifying Start/End Day Constraints (No Empty Days)...")
    sections = Section.objects.all()[:5]
    for section in sections:
        entries = ScheduleEntry.objects.filter(schedule=schedule, section=section)
        days = set(entries.values_list('timeslot__day', flat=True))
        
        print(f"   Section {section.class_id}: {len(days)} days with classes {list(days)}")
        expected_days = {'MON', 'TUE', 'WED', 'THU', 'FRI'}
        missing = expected_days - days
        if missing:
             total_hours = entries.count()
             print(f"     WARNING: Empty days detected: {missing} (Total Hours: {total_hours})")
        else:
            print(f"     PASS: All days have classes.")

    print("\n2. Verifying Elective Assignments...")
    ea_count = ElectiveAssignment.objects.filter(schedule=schedule).count()
    print(f"   Elective Assignments created: {ea_count}")

    print("\n3. Debugging Conflicts API...")
    User = get_user_model()
    user, _ = User.objects.get_or_create(email='verifier@test.com', defaults={'first_name':'Verifier', 'last_name':'Bot'})
    user.is_superuser = True
    user.is_staff = True
    user.save()
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    url = f'/api/scheduler/validate/{schedule.schedule_id}/'
    print(f"   Calling {url}...")
    response = client.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Validation Status: {data.get('valid')}")
        print(f"   Conflicts Found: {len(data.get('conflicts', []))}")
        for c in data.get('conflicts', [])[:5]:
            print(f"   - {c}")
    else:
        print(f"   API Call Failed: {response.status_code}")
        # Print first 500 chars of content to debug
        print(f"   Error Content (Preview): {response.content.decode('utf-8')[:500]}")

if __name__ == '__main__':
    verify_results()
