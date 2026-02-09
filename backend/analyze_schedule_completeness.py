
import os
import django
import sys
from django.db.models import Sum, Count, F

# Setup Django environment
sys.path.append('/Users/Vamsi/Desktop/SE/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Schedule, Section, Course, ScheduleEntry, Teacher, TeacherCourseMapping, Room
from scheduler.algorithm import calculate_schedule_quality

# Get recent schedules
schedules = Schedule.objects.order_by('-created_at')[:3]
print("\n--- Recent Schedules ---")
for s in schedules:
    count = ScheduleEntry.objects.filter(schedule=s).count()
    print(f"ID {s.schedule_id}: {s.name} ({s.semester} {s.year}) - Entries: {count}, Score: {s.quality_score}")

# Analyze the one with most entries (assuming that's the one user is looking at, or the latest viable one)
# Or just analyze the first one if it has entries.
schedule = schedules.first()
if schedule.entries.count() == 0 and len(schedules) > 1:
     print("Latest schedule has 0 entries. Checking previous...")
     schedule = schedules[1]

# detailed section analysis
print("\n--- Section Completeness Analysis ---")
sections = Section.objects.all().order_by('year', 'class_id')

low_completion_sections = []

for section in sections:
    # Calculate required slots
    # Get all courses for this section's year/semester
    courses = Course.objects.filter(
        year=section.year,
        semester=schedule.semester,
        is_elective=False
    )
    
    total_required = courses.aggregate(total=Sum('weekly_slots'))['total'] or 0
    
    # Calculate scheduled slots
    scheduled = ScheduleEntry.objects.filter(
        schedule=schedule,
        section=section
    ).count()
    
    if total_required > 0:
        percentage = (scheduled / total_required) * 100
    else:
        percentage = 100.0 # No courses needed?
        
    print(f"Section {section.class_id} (Year {section.year}): {scheduled}/{total_required} slots ({percentage:.1f}%)")
    
    if percentage < 90:
        low_completion_sections.append({
            'section': section,
            'missing': total_required - scheduled,
            'courses': courses
        })

print(f"\nTotal Sections with < 90% completion: {len(low_completion_sections)}")

if low_completion_sections:
    bad_case = low_completion_sections[0]
    section = bad_case['section']
    print(f"\n--- Deep Dive: {section.class_id} ---")
    print("Missing Courses (checking mappings):")
    
    for course in bad_case['courses']:
        count = ScheduleEntry.objects.filter(schedule=schedule, section=section, course=course).count()
        req = course.weekly_slots
        if count < req:
            print(f" - {course.course_name} ({course.course_id}): {count}/{req} scheduled.")
            
            # Check Mappings
            mappings = TeacherCourseMapping.objects.filter(course=course)
            map_count = mappings.count()
            print(f"   Mappings found in DB: {map_count}")
            if map_count > 0:
                teachers = [m.teacher.teacher_name for m in mappings[:3]]
                print(f"   Mapped Teachers: {', '.join(teachers)}")
            else:
                print("   CRITICAL: No teachers mapped to this course!")

from core.models import Schedule, Section, Course, ScheduleEntry, Teacher, TeacherCourseMapping, Room, ConflictLog
from scheduler.algorithm import calculate_schedule_quality

# ... (rest of code) ...

# Check Conflicts
print("\n--- Conflict Summary ---")
conflicts = ConflictLog.objects.filter(schedule=schedule).values('conflict_type').annotate(count=Count('id'))
for c in conflicts:
    print(f"{c['conflict_type']}: {c['count']}")

# Check Room Capacity vs Demand
print("\n--- Capacity Analysis ---")
total_classrooms = Room.objects.filter(room_type='CLASSROOM').count()
total_slots = 40 # Standard
total_capacity = total_classrooms * total_slots
print(f"Total Classrooms: {total_classrooms}")
print(f"Total Theoretical Capacity: {total_capacity} slots")

# Calculate Total Demand
total_demand = 0
sections = Section.objects.all()
for section in sections:
    courses = Course.objects.filter(year=section.year, semester=schedule.semester, is_elective=False)
    # Filter theory slots
    for c in courses:
        lab = c.practicals if (c.is_lab or c.practicals>0) else 0
        theory = c.weekly_slots - lab
        total_demand += theory

print(f"Total Theory Slot Demand: {total_demand}")
if total_demand > total_capacity:
    print(f"CRITICAL: Demand exceeds Capacity by {total_demand - total_capacity} slots!")
else:
    print(f"Capacity Surplus: {total_capacity - total_demand} slots")

print("\n--- Teacher Capacity Analysis ---")
teachers = Teacher.objects.all()
total_teacher_hours = teachers.aggregate(total=Sum('max_hours_per_week'))['total'] or 0
teacher_count = teachers.count()
print(f"Total Teachers: {teacher_count}")
print(f"Total Max Teaching Hours: {total_teacher_hours}")
print(f"Total Course Demand (Theory + Lab): {total_demand}") # Wait, total_demand above was Theory only?

# Recalculate Total Demand fully
full_demand = 0
for section in Section.objects.all():
    courses = Course.objects.filter(year=section.year, semester=schedule.semester, is_elective=False)
    for c in courses:
        full_demand += c.weekly_slots # Both Theory and Lab

print(f"Total Required Teaching Hours (Slots): {full_demand}")

if full_demand > total_teacher_hours:
    print(f"CRITICAL: Teacher Shortage! Need {full_demand - total_teacher_hours} more hours.")
    print(f"Approx {int((full_demand - total_teacher_hours)/15)} more teachers needed (at 15h/week).")
else:
    print(f"Teacher Capacity Surplus: {total_teacher_hours - full_demand} hours")

print("\n--- Teacher Utilization Stats ---")
overloaded_teachers = []
teachers = Teacher.objects.all()
for t in teachers:
    load = ScheduleEntry.objects.filter(schedule=schedule, teacher=t).count()
    if load >= t.max_hours_per_week:
         overloaded_teachers.append((t, load))
    # print(f"{t.teacher_id}: {load}/{t.max_hours_per_week}")

print(f"Teachers at or exceeding max capacity: {len(overloaded_teachers)}")
for t, load in overloaded_teachers[:10]:
    print(f" - {t.teacher_name}: {load}/{t.max_hours_per_week}")

print("\n--- Department Analysis ---")
deps = Teacher.objects.values('department').annotate(
    count=Count('teacher_id'),
    total_max=Sum('max_hours_per_week')
)
for d in deps:
    print(f"Dept: {d['department']} - Teachers: {d['count']}, Capacity: {d['total_max']}")
