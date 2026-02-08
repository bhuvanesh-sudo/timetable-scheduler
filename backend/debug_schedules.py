import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule

schedules = Schedule.objects.all().order_by('-created_at')
for s in schedules:
    print(f"ID: {s.schedule_id}, Name: '{s.name}', Year: {s.year}, Sem: {s.semester}, Created: {s.created_at}")
