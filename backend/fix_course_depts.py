
import os
import django
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Course, TeacherCourseMapping, Teacher

def populate():
    print("Populating Course departments...")
    courses = Course.objects.all()
    updated_count = 0
    
    for c in courses:
        # Try to infer from course_id (e.g., 23CSE111)
        match = re.search(r'[A-Z]{3}', c.course_id)
        if match:
            dept = match.group()
            c.department = dept
            c.save()
            updated_count += 1
            print(f"Course {c.course_id} assigned to {dept}")
        else:
            # Try to infer from mappings
            mappings = TeacherCourseMapping.objects.filter(course=c)
            if mappings.exists():
                # Take department of the first teacher mapped
                dept = mappings.first().teacher.department
                if dept:
                    c.department = dept
                    c.save()
                    updated_count += 1
                    print(f"Course {c.course_id} assigned to {dept} (via Teacher Mapping)")

    print(f"Successfully updated {updated_count} courses.")

if __name__ == "__main__":
    populate()
