import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Section, Course, Teacher, Room, TimeSlot, TeacherCourseMapping

def diagnose():
    sections = Section.objects.all()
    total_sections = sections.count()
    total_rooms = Room.objects.count()
    classrooms = Room.objects.filter(room_type='CLASSROOM').count()
    labs = Room.objects.filter(room_type='LAB').count()
    total_teachers = Teacher.objects.count()
    total_timeslots = TimeSlot.objects.count()
    
    print(f"--- GLOBAL STATS ---")
    print(f"Sections: {total_sections}")
    print(f"Rooms: {total_rooms} (Classrooms: {classrooms}, Labs: {labs})")
    print(f"Teachers: {total_teachers}")
    print(f"TimeSlots per section: {total_timeslots}")
    print(f"Total Slot Capacity (Rooms * TimeSlots): {total_rooms * total_timeslots}")
    
    print(f"\n--- SECTION DEMAND (ACTUAL ALGO LOGIC) ---")
    total_demand = 0
    theory_demand = 0
    lab_demand = 0
    
    schedule_semester = 'even' # Analyzed odd before, now even
    print(f"--- ANALYZING SEMESTER: {schedule_semester.upper()} ---")
    for sec in sections:
        sec_total = 0
        sec_theory = 0
        sec_lab = 0
        courses = Course.objects.filter(year=sec.year, semester=schedule_semester, is_schedulable=True)
        for c in courses:
            if c.is_lab:
                # Stage 1 logic
                sec_lab += c.practicals
                sec_total += c.practicals
            else:
                # Stage 2 logic
                sec_theory += c.weekly_slots
                sec_total += c.weekly_slots
        
        print(f"Section {sec.class_id}: Total {sec_total} (Theory: {sec_theory}, Lab: {sec_lab})")
        total_demand += sec_total
        theory_demand += sec_theory
        lab_demand += sec_lab
        if sec_total > total_timeslots:
            print(f"  WARNING: Section {sec.class_id} demand ({sec_total}) exceeds available timeslots ({total_timeslots})!")
            
    print(f"\n--- RESOURCE SUMMARY ---")
    print(f"Total Theory Demand: {theory_demand}")
    print(f"Total Theory Capacity (Classrooms * TimeSlots): {classrooms * total_timeslots}")
    print(f"Total Lab Demand: {lab_demand}")
    print(f"Total Lab Capacity (Labs * TimeSlots): {labs * total_timeslots}")
    
    if theory_demand > classrooms * total_timeslots:
        print(f"  CRITICAL: Insufficient Classrooms!")
    if lab_demand > labs * total_timeslots:
        print(f"  CRITICAL: Insufficient Labs!")

    print(f"\n--- TEACHER CAPACITY ---")
    teacher_demand = {}
    for sec in sections:
        courses = Course.objects.filter(year=sec.year, is_schedulable=True, is_elective=False)
        for c in courses:
            mappings = TeacherCourseMapping.objects.filter(course=c)
            # This is complex because one course can have multiple teachers mapped but only one assigned.
            # But the algorithm preallocates.
    
    # Just check if any course has NO teacher mapped
    for c in Course.objects.filter(is_schedulable=True, is_elective=False):
        if not TeacherCourseMapping.objects.filter(course=c).exists():
            print(f"  WARNING: Course {c.course_id} has NO teacher mapped!")

if __name__ == "__main__":
    diagnose()
