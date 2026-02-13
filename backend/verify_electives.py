import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import ScheduleEntry, ElectiveAssignment, ElectiveAllocation, Section
from django.db.models import Count

entry_count = ScheduleEntry.objects.count()
bucket_entries = ScheduleEntry.objects.filter(course__is_elective=True, course__is_schedulable=True)
bucket_count = bucket_entries.count()
expansion_count = ElectiveAssignment.objects.count()

print(f'Total Entries: {entry_count}')
print(f'Bucket Entries (Elective Slots): {bucket_count}')
print(f'Elective Expansions (Topics): {expansion_count}')

# Room sharing check
shared_rooms = ElectiveAssignment.objects.values('timeslot', 'room', 'course').annotate(section_count=Count('section')).filter(section_count__gt=1)
print(f'\nTotal shared Topic-Room-Time slots: {shared_rooms.count()}')
for s in shared_rooms[:5]:
    room_id = s['room']
    timeslot_id = s['timeslot']
    course_id = s['course']
    print(f"Room {room_id} at Slot {timeslot_id} shared by {s['section_count']} sections for Course {course_id}")

if bucket_count > 0:
    bucket = bucket_entries.first()
    # ... (rest of old code if needed, but the above is enough)
