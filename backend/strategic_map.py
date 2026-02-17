import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Teacher, TeacherCourseMapping, Course, Section
from django.db import transaction
from django.db.models import Count

def strategic_map():
    target_sem = 'even'
    print(f"--- Strategic Mapping for {target_sem} Semester ---")
    
    # 1. Identify courses with the highest demand (weekly_slots * sections)
    even_courses = Course.objects.filter(semester=target_sem, is_schedulable=True)
    course_demands = []
    for c in even_courses:
        # Number of sections this course is for (approximate by year matching)
        sec_count = Section.objects.filter(year=c.year).count()
        demand = c.weekly_slots * sec_count
        course_demands.append((c, demand))
    
    # Sort by demand descending
    course_demands.sort(key=lambda x: x[1], reverse=True)
    high_demand_ids = [c.course_id for c, d in course_demands[:10]]
    print(f"High Demand Courses: {high_demand_ids}")

    # 2. Get all teachers
    teachers = Teacher.objects.all()
    
    # 3. Clear 'even' mappings for these teachers to avoid junk
    with transaction.atomic():
        TeacherCourseMapping.objects.filter(course__semester=target_sem).delete()
        
        # 4. Map every teacher to at least 15 courses
        # This gives the scheduler maximum flexibility to fill 40% workload and 5-day presence
        even_courses_list = list(even_courses)
        for i, t in enumerate(teachers):
            # All teachers get the High Demand courses first
            # but in different preference orders (not implemented here but the list order matters slightly)
            mapped_courses = []
            
            # Start with some high demand ones
            h_indices = [(i + j) % len(course_demands) for j in range(15)]
            for idx in h_indices:
                mapped_courses.append(course_demands[idx][0])
            
            # Add department courses if they aren't already there
            dept_courses = [c for c in even_courses_list if c.course_id.startswith(t.department[:3])]
            for c in dept_courses:
                if len(mapped_courses) >= 20: break # Max 20 mappings
                if c not in mapped_courses:
                    mapped_courses.append(c)
            
            for c in mapped_courses:
                TeacherCourseMapping.objects.get_or_create(
                    teacher=t,
                    course=c,
                    defaults={'preference_level': 3}
                )
    
    print(f"Successfully mapped {teachers.count()} teachers strategically.")

if __name__ == "__main__":
    strategic_map()
