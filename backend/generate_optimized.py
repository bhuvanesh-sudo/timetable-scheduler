
import os
import django
import sys
import time

# Setup Django environment
sys.path.append('/Users/Vamsi/Desktop/SE/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule
from scheduler.algorithm import generate_schedule

print("Creating Optimized Schedule...")
schedule = Schedule.objects.create(
    name="Optimized Schedule " + str(int(time.time())),
    semester="odd", 
    year=2024,
    status="PENDING"
)

print(f"Generating schedule {schedule.schedule_id}...")
start_time = time.time()
success, message = generate_schedule(schedule.schedule_id)
end_time = time.time()

print(f"Generation completed in {end_time - start_time:.2f} seconds")
print(f"Success: {success}")
print(f"Message: {message}")
