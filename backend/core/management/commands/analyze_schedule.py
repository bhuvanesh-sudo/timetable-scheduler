from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from core.models import Schedule, Section, Course, ScheduleEntry, Teacher, TeacherCourseMapping, Room, ConflictLog

class Command(BaseCommand):
    help = 'Analyzes the completeness and quality of the latest schedule'

    def handle(self, *args, **options):
        # Get recent schedules
        schedules = Schedule.objects.order_by('-created_at')[:3]
        self.stdout.write("\n--- Recent Schedules ---")
        for s in schedules:
            count = ScheduleEntry.objects.filter(schedule=s).count()
            self.stdout.write(f"ID {s.schedule_id}: {s.name} ({s.semester} {s.year}) - Entries: {count}, Score: {s.quality_score}")

        if not schedules.exists():
            self.stdout.write("No schedules found.")
            return

        # Analyze the one with most entries or the first one
        schedule = schedules.first()
        if schedule.entries.count() == 0 and len(schedules) > 1:
             self.stdout.write("Latest schedule has 0 entries. Checking previous...")
             schedule = schedules[1]
        
        self.stdout.write(f"\nAnalyzing Schedule: {schedule.name} (ID: {schedule.schedule_id})")

        # detailed section analysis
        self.stdout.write("\n--- Section Completeness Analysis ---")
        sections = Section.objects.all().order_by('year', 'class_id')
        
        low_completion_sections = []
        
        for section in sections:
            # Calculate required slots
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
                percentage = 100.0 # No courses needed
                
            self.stdout.write(f"Section {section.class_id} (Year {section.year}): {scheduled}/{total_required} slots ({percentage:.1f}%)")
            
            if percentage < 90:
                low_completion_sections.append({
                    'section': section,
                    'missing': total_required - scheduled,
                    'courses': courses
                })
        
        self.stdout.write(f"\nTotal Sections with < 90% completion: {len(low_completion_sections)}")
        
        if low_completion_sections:
            bad_case = low_completion_sections[0]
            section = bad_case['section']
            self.stdout.write(f"\n--- Deep Dive: {section.class_id} ---")
            self.stdout.write("Missing Courses (checking mappings):")
            
            for course in bad_case['courses']:
                count = ScheduleEntry.objects.filter(schedule=schedule, section=section, course=course).count()
                req = course.weekly_slots
                if count < req:
                    self.stdout.write(f" - {course.course_name} ({course.course_id}): {count}/{req} scheduled.")
                    
                    # Check Mappings
                    mappings = TeacherCourseMapping.objects.filter(course=course)
                    map_count = mappings.count()
                    self.stdout.write(f"   Mappings found in DB: {map_count}")
                    if map_count > 0:
                        teachers = [m.teacher.teacher_name for m in mappings[:3]]
                        self.stdout.write(f"   Mapped Teachers: {', '.join(teachers)}")
                    else:
                        self.stdout.write("   CRITICAL: No teachers mapped to this course!")

        # Check Conflicts
        self.stdout.write("\n--- Conflict Summary ---")
        conflicts = ConflictLog.objects.filter(schedule=schedule).values('conflict_type').annotate(count=Count('id'))
        for c in conflicts:
            self.stdout.write(f"{c['conflict_type']}: {c['count']}")

        # Check Room Capacity vs Demand
        self.stdout.write("\n--- Capacity Analysis ---")
        total_classrooms = Room.objects.filter(room_type='CLASSROOM').count()
        total_slots = 40 # Standard
        total_capacity = total_classrooms * total_slots
        self.stdout.write(f"Total Classrooms: {total_classrooms}")
        self.stdout.write(f"Total Theoretical Capacity: {total_capacity} slots")
        
        # Calculate Total Demand (Theory Only)
        total_demand = 0
        sections = Section.objects.all()
        for section in sections:
            courses = Course.objects.filter(year=section.year, semester=schedule.semester, is_elective=False)
            for c in courses:
                lab = c.practicals if (c.is_lab or c.practicals > 0) else 0
                theory = c.weekly_slots - lab
                total_demand += theory
        
        self.stdout.write(f"Total Theory Slot Demand: {total_demand}")
        if total_demand > total_capacity:
            self.stdout.write(f"CRITICAL: Demand exceeds Capacity by {total_demand - total_capacity} slots!")
        else:
            self.stdout.write(f"Capacity Surplus: {total_capacity - total_demand} slots")

        self.stdout.write("\n--- Teacher Capacity Analysis ---")
        teachers = Teacher.objects.all()
        total_teacher_hours = teachers.aggregate(total=Sum('max_hours_per_week'))['total'] or 0
        teacher_count = teachers.count()
        self.stdout.write(f"Total Teachers: {teacher_count}")
        self.stdout.write(f"Total Max Teaching Hours: {total_teacher_hours}")
        
        # Recalculate Total Demand fully (Theory + Lab)
        full_demand = 0
        for section in Section.objects.all():
            courses = Course.objects.filter(year=section.year, semester=schedule.semester, is_elective=False)
            for c in courses:
                full_demand += c.weekly_slots
                
        self.stdout.write(f"Total Required Teaching Hours (Slots): {full_demand}")
        
        if full_demand > total_teacher_hours:
            self.stdout.write(f"CRITICAL: Teacher Shortage! Need {full_demand - total_teacher_hours} more hours.")
        else:
            self.stdout.write(f"Teacher Capacity Surplus: {total_teacher_hours - full_demand} hours")

        self.stdout.write("\n--- Teacher Utilization Stats ---")
        overloaded_teachers = []
        for t in teachers:
            load = ScheduleEntry.objects.filter(schedule=schedule, teacher=t).count()
            if load >= t.max_hours_per_week:
                 overloaded_teachers.append((t, load))
        
        self.stdout.write(f"Teachers at or exceeding max capacity: {len(overloaded_teachers)}")
        for t, load in overloaded_teachers[:10]:
            self.stdout.write(f" - {t.teacher_name}: {load}/{t.max_hours_per_week}")

        self.stdout.write("\n--- Department Analysis ---")
        deps = Teacher.objects.values('department').annotate(
            count=Count('teacher_id'),
            total_max=Sum('max_hours_per_week')
        )
        for d in deps:
            self.stdout.write(f"Dept: {d['department']} - Teachers: {d['count']}, Capacity: {d['total_max']}")
