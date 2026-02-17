import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Teacher, TeacherCourseMapping, Course, Section
from django.db import transaction

def auto_map_faculty():
    target_sem = 'even'
    print(f"--- Auto-Mapping Faculty for Semester: {target_sem} ---")
    
    # 1. Get all courses for this semester that are schedulable
    even_courses = Course.objects.filter(semester=target_sem, is_schedulable=True)
    department_courses = {}
    for c in even_courses:
        # Simplistic department matching (CSE courses to CSE dept, etc)
        # Assuming course_id prefix or looking at and mapping them
        dept = 'CSE' # Default for this project based on data
        if c.course_id.startswith('MAT'): dept = 'MAT'
        if c.course_id.startswith('PHY'): dept = 'PHY'
        # Add to department map
        if dept not in department_courses: department_courses[dept] = []
        department_courses[dept].append(c)

    # 2. Find teachers with no mappings for this semester
    teachers = Teacher.objects.all()
    unmapped_count = 0
    course_usage = {c.course_id: 0 for c in even_courses}
    
    with transaction.atomic():
        for t in teachers:
            sem_maps = TeacherCourseMapping.objects.filter(teacher=t, course__semester=target_sem)
            if not sem_maps.exists():
                dept = t.department if t.department in department_courses else 'CSE'
                courses_to_map = department_courses.get(dept, [])
                if not courses_to_map:
                    courses_to_map = department_courses.get('CSE', [])
                
                if courses_to_map:
                    # Sort courses by usage (ascending) to spread mapping
                    courses_to_map.sort(key=lambda c: course_usage[c.course_id])
                    
                    # Map to 3 courses to give more flexibility
                    for c in courses_to_map[:3]:
                        TeacherCourseMapping.objects.get_or_create(
                            teacher=t,
                            course=c,
                            defaults={'preference_level': 3}
                        )
                        course_usage[c.course_id] += 1
                    
                    unmapped_count += 1
                    print(f"  Mapped {t.teacher_name} ({t.department}) to {courses_to_map[0].course_id}, {courses_to_map[1].course_id}...")

    print(f"\nFinished: Redistributed mappings for {unmapped_count} faculty members.")

if __name__ == "__main__":
    auto_map_faculty()
