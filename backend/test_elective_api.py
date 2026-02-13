
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.get(username='admin')

from core.models import Schedule, ElectiveAssignment

def test_api():
    client = APIClient()
    client.force_authenticate(user=admin)
    
    # Get a schedule
    schedule = Schedule.objects.last()
    if not schedule:
        print("No schedule found. Cannot test API.")
        return

    print(f"Testing with Schedule ID: {schedule.schedule_id}")
    
    # Call the new API
    response = client.get(f'/api/scheduler/elective-assignments/?schedule_id={schedule.schedule_id}')
    
    if response.status_code == 200:
        data = response.json()
        print(f"API Call Successful. Records returned: {len(data)}")
        if len(data) > 0:
            print("Sample Record Keys:", data[0].keys())
            print("Sample Record:", json.dumps(data[0], indent=2))
            
            # Verify required fields
            req_fields = ['room', 'teacher_name', 'course_name', 'time']
            if all(f in data[0] for f in req_fields):
                print("PASS: All required fields present.")
            else:
                print("FAIL: Missing fields.")
        else:
            print("WARNING: No elective assignments found for this schedule.")
    else:
        print(f"FAIL: API Error {response.status_code}")
        print(response.content)

if __name__ == '__main__':
    test_api()
