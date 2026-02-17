import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Teacher, TeacherCourseMapping, ScheduleEntry, ElectiveAssignment, Schedule, Course

def run_diagnostic():
    s = Schedule.objects.latest('schedule_id')
    print(f"Checking load for Schedule: {s.name}")
    
    teachers = Teacher.objects.all()
    zero_teachers = []
    for t in teachers:
        has_load = ScheduleEntry.objects.filter(schedule=s, teacher=t).exists() or \
                   ElectiveAssignment.objects.filter(schedule=s, teacher=t).exists()
        if not has_load:
            zero_teachers.append(t)
            
    print(f"Zero Load Teachers: {len(zero_teachers)}")
    for t in zero_teachers[:15]:
        mappings = TeacherCourseMapping.objects.filter(teacher=t).select_related('course')
        course_ids = [m.course.course_id for m in mappings]
        # Are these courses even in the current semester?
        sem_courses = [m.course.course_id for m in mappings if m.course.semester == s.semester]
        print(f"  - {t.teacher_name} ({t.department}): Mapped to {course_ids}. Sem matches: {sem_courses}")

    print("\n--- Courses failing with OVERLOAD_PREVENTED ---")
    from core.models import ConflictLog
    overloads = ConflictLog.objects.filter(schedule=s, conflict_type='OVERLOAD_PREVENTED')
    fail_courses = {}
    for o in overloads:
        import re
        match = re.search(r'teacher for ([\w\-]+)', o.description)
        if match:
            cid = match.group(1)
            fail_courses[cid] = fail_courses.get(cid, 0) + 1
            
    for cid, count in fail_courses.items():
        mapped_teachers = TeacherCourseMapping.objects.filter(course_id=cid).values_list('teacher__teacher_name', flat=True)
        print(f"Course {cid} failed {count} times. Mapped to: {list(mapped_teachers)}")

    print("\n--- Core Courses with NO mappings for current semester ---")
    even_courses = Course.objects.filter(semester=s.semester, is_schedulable=True, is_elective=False)
    for c in even_courses:
        maps = TeacherCourseMapping.objects.filter(course=c).count()
        if maps == 0:
            print(f"  - {c.course_id} ({c.course_name}): 0 Mappings!")
        elif maps < 2:
            mapped = list(TeacherCourseMapping.objects.filter(course=c).values_list('teacher__teacher_name', flat=True))
            print(f"  - {c.course_id} ({c.course_name}): Only {maps} mapping: {mapped}")

if __name__ == "__main__":
    run_diagnostic()
