"""
Core Scheduling Algorithm for M3 Timetable System

This module implements the main scheduling algorithm using a greedy approach
with backtracking and constraint satisfaction.

Algorithm: Greedy with Backtracking
- Iterates through sections and their required courses
- For each course, tries to find valid (teacher, room, timeslot) combinations
- Uses constraint validation to ensure no conflicts
- Backtracks if no valid assignment is found

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

import random
from datetime import datetime
from django.db import transaction
from core.models import (
    Schedule, ScheduleEntry, Section, Course, Teacher, Room,
    TimeSlot, TeacherCourseMapping, ConflictLog
)
from .constraints import ConstraintValidator, calculate_schedule_quality


class TimetableScheduler:
    """
    Main scheduling algorithm class.
    Generates conflict-free timetables using constraint programming.
    """
    
    def __init__(self, schedule):
        """
        Initialize scheduler with a schedule object.
        
        Args:
            schedule: Schedule object to populate
        """
        self.schedule = schedule
        self.validator = ConstraintValidator(schedule)
        self.conflicts = []
        # Teacher-section pre-allocation: maps (course_id, section_id) -> teacher
        self.teacher_assignments = {}
    
    def generate(self):
        """
        Main entry point for schedule generation.
        Generates schedules for ALL 4 years simultaneously to ensure
        no teacher/room conflicts across years.
        
        Returns:
            tuple: (success, message)
        """
        try:
            # Update schedule status
            self.schedule.status = 'GENERATING'
            self.schedule.save()
            
            # Get all sections (sections exist across both odd and even semesters)
            # The semester is determined by which courses are available, not the section itself
            sections = Section.objects.all().order_by('year', 'class_id')
            
            if not sections.exists():
                return False, f"No sections found for semester {self.schedule.semester}"
            
            # Get all available timeslots
            timeslots = list(TimeSlot.objects.all().order_by('day', 'slot_number'))
            
            if not timeslots:
                return False, "No timeslots available"
            
            # Count sections by year for reporting
            year_counts = {}
            for section in sections:
                year_counts[section.year] = year_counts.get(section.year, 0) + 1
            
            # PRE-ALLOCATE TEACHERS: Assign teachers to section-course pairs
            self._preallocate_teachers(sections)
            
            # PHASE 1: LABS - Schedule Labs for ALL Sections First (Hard Constraint)
            # This ensures continuous blocks can be found before theory slots fragment the schedule
            for section in sections:
                self._schedule_section_labs(section, timeslots)

            # PHASE 2: THEORY - Schedule Theory for ALL Sections
            for section in sections:
                self._schedule_section_theory(section, timeslots)
            
            # Calculate quality score
            quality = calculate_schedule_quality(self.schedule)
            self.schedule.quality_score = quality
            self.schedule.status = 'COMPLETED'
            self.schedule.completed_at = datetime.now()
            self.schedule.save()
            
            # Build success message with year breakdown
            years_scheduled = ', '.join([f"Year {y}: {count} sections" for y, count in sorted(year_counts.items())])
            return True, f"Schedule generated for all years ({years_scheduled}) with quality score: {quality:.2f}"
        
        except Exception as e:
            self.schedule.status = 'FAILED'
            self.schedule.save()
            return False, f"Error during scheduling: {str(e)}"
    
    def _preallocate_teachers(self, sections):
        """
        Pre-allocate teachers using the 4+2 rule:
        - For each course (across 8 sections of a year/sem):
        - 6 distinct teachers available (from mappings).
        - First 4 teachers -> 1 section each.
        - Next 2 teachers -> 2 sections each.
        - Total 8 sections covered.
        """
        from collections import defaultdict
        
        # Group sections by year
        sections_by_year = defaultdict(list)
        for section in sections:
            sections_by_year[section.year].append(section)
            
        # Process each year
        for year, year_sections in sections_by_year.items():
            # Get courses for this year/semester
            courses = Course.objects.filter(
                year=year,
                semester=self.schedule.semester,
                is_elective=False
            )
            
            for course in courses:
                # Get mapped teachers
                mappings = list(TeacherCourseMapping.objects.filter(
                    course=course
                ).select_related('teacher').order_by('-preference_level'))
                
                # Get distinct teachers
                distinct_teachers = []
                seen_ids = set()
                for m in mappings:
                    if m.teacher.teacher_id not in seen_ids:
                        distinct_teachers.append(m.teacher)
                        seen_ids.add(m.teacher.teacher_id)
                
                if not distinct_teachers:
                    continue
                
                # Sort teachers (randomize for fairness)
                random.shuffle(distinct_teachers)
                
                # Create allocation queue based on 4+2 rule
                allocation_queue = []
                
                # First 4 teachers get 1 slot
                for i in range(min(4, len(distinct_teachers))):
                    allocation_queue.append(distinct_teachers[i])
                    
                # Remaining teachers get 2 slots
                for i in range(4, len(distinct_teachers)):
                    allocation_queue.append(distinct_teachers[i])
                    allocation_queue.append(distinct_teachers[i])
                
                # Assign to sections
                for i, section in enumerate(year_sections):
                    if i < len(allocation_queue):
                        teacher = allocation_queue[i]
                    else:
                        # Fallback: Round robin
                        teacher = distinct_teachers[i % len(distinct_teachers)]
                    
                    self.teacher_assignments[(course.course_id, section.class_id)] = teacher

    def _schedule_section_labs(self, section, timeslots):
        """
        Phase 1: Schedule Lab Blocks (Hardest Constraint)
        """
        courses = Course.objects.filter(
            year=section.year,
            semester=self.schedule.semester,
            is_elective=False
        )
        
        for course in courses:
            # Determine Lab Slots
            lab_slots = course.practicals if (course.is_lab or course.practicals > 0) else 0
            if lab_slots == 0:
                continue
            
            # Identify Teacher
            assignment_key = (course.course_id, section.class_id)
            teacher = self.teacher_assignments.get(assignment_key)
            if not teacher:
                # Fallback
                mappings = TeacherCourseMapping.objects.filter(course=course).order_by('-preference_level')
                if mappings.exists():
                    teacher = mappings.first().teacher
                else:
                    self._log_conflict('NO_TEACHER', f"No teacher for {course.course_id} (Lab)", 'HIGH')
                    continue

            # Check if likely already scheduled (if re-running?)
            # We assume fresh generation.
            
            block_assigned = False
            
            # Group timeslots by day
            slots_by_day = {}
            for ts in timeslots:
                if ts.day not in slots_by_day:
                    slots_by_day[ts.day] = []
                slots_by_day[ts.day].append(ts)
            
            days = list(slots_by_day.keys())
            random.shuffle(days)
            
            for day in days:
                day_slots = sorted(slots_by_day[day], key=lambda x: x.slot_number)
                # Try to find consecutive window
                for i in range(len(day_slots) - lab_slots + 1):
                    window = day_slots[i : i + lab_slots]
                    
                    # Validate continuity
                    is_continuous = True
                    for k in range(len(window) - 1):
                        if window[k+1].slot_number != window[k].slot_number + 1:
                            is_continuous = False
                            break
                    if not is_continuous: continue

                    # Validate availability
                    if self._can_schedule_block(window, section, course, teacher):
                         # Pick Room
                         valid_room = self._find_block_room(window, course)
                         if valid_room:
                             for ts in window:
                                 ScheduleEntry.objects.create(
                                     schedule=self.schedule,
                                     section=section,
                                     course=course,
                                     teacher=teacher,
                                     room=valid_room,
                                     timeslot=ts,
                                     is_lab_session=True
                                 )
                             block_assigned = True
                             self.validator = ConstraintValidator(self.schedule)
                             break
                if block_assigned: break
            
            if not block_assigned:
                self._log_conflict('LAB_BLOCK_FAILED', f"Failed to assign lab block for {course.course_id}", 'HIGH')

    def _schedule_section_theory(self, section, timeslots):
        """
        Phase 2: Schedule Theory Slots (Fill remaining)
        """
        courses = Course.objects.filter(
            year=section.year,
            semester=self.schedule.semester,
            is_elective=False
        )
        
        for course in courses:
            # Check how many slots already scheduled (Labs)
            current_slots = ScheduleEntry.objects.filter(
                schedule=self.schedule,
                section=section,
                course=course
            ).count()
            
            needed = course.weekly_slots - current_slots
            if needed <= 0:
                continue
            
            # Identify Teacher
            assignment_key = (course.course_id, section.class_id)
            teacher = self.teacher_assignments.get(assignment_key)
            if not teacher:
                # Fallback
                mappings = TeacherCourseMapping.objects.filter(course=course).order_by('-preference_level')
                if mappings.exists():
                    teacher = mappings.first().teacher
                else:
                    self._log_conflict('NO_TEACHER', f"No teacher for {course.course_id}", 'HIGH')
                    continue
            
            slots_scheduled = 0
            available_slots = list(timeslots)
            random.shuffle(available_slots)
            
            for timeslot in available_slots:
                if slots_scheduled >= needed:
                    break
                
                room = self._find_suitable_room(course, timeslot)
                if not room: continue
                
                is_valid, _ = self.validator.validate_all(section, course, teacher, room, timeslot)
                if is_valid:
                    ScheduleEntry.objects.create(
                        schedule=self.schedule,
                        section=section,
                        course=course,
                        teacher=teacher,
                        room=room,
                        timeslot=timeslot,
                        is_lab_session=False
                    )
                    slots_scheduled += 1
                    self.validator = ConstraintValidator(self.schedule)
            
    def _can_schedule_block(self, window, section, course, teacher):
        """Check if a block of slots is valid for teacher/section."""
        for ts in window:
            # Check if Teacher and Section are free at this timeslot
            # We allocate Room later, so we only check person availability here
            
            t_valid, _ = self.validator.validate_faculty_availability(teacher, ts)
            if not t_valid: return False
            
            s_valid, _ = self.validator.validate_section_availability(section, ts)
            if not s_valid: return False
            
        return True

    def _find_block_room(self, window, course):
        """Find a room available for ALL slots in window."""
        room_type = 'LAB' if (course.is_lab or course.practicals > 0) else 'CLASSROOM'
        rooms = list(Room.objects.filter(room_type=room_type))
        random.shuffle(rooms)
        
        for room in rooms:
            available = True
            for ts in window:
                r_valid, _ = self.validator.validate_room_availability(room, ts)
                if not r_valid:
                    available = False
                    break
            if available:
                return room
        return None
    
    def _find_suitable_room(self, course, timeslot):
        """
        Find a suitable room for a course at a given timeslot.
        
        Args:
            course: Course object
            timeslot: TimeSlot object
        
        Returns:
            Room object or None
        """
        # Determine required room type
        if course.is_lab:
            room_type = 'LAB'
        else:
            room_type = 'CLASSROOM'
        
        # Get all rooms of the required type
        rooms = Room.objects.filter(room_type=room_type)
        
        # Shuffle for variety
        rooms = list(rooms)
        random.shuffle(rooms)
        
        # Find first available room
        for room in rooms:
            is_valid, _ = self.validator.validate_room_availability(room, timeslot)
            if is_valid:
                return room
        
        return None
    
    def _log_conflict(self, conflict_type, description, severity):
        """
        Log a conflict to the database.
        
        Args:
            conflict_type: Type of conflict
            description: Detailed description
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        """
        ConflictLog.objects.create(
            schedule=self.schedule,
            conflict_type=conflict_type,
            description=description,
            severity=severity
        )
        self.conflicts.append(description)


def generate_schedule(schedule_id):
    """
    Convenience function to generate a schedule by ID.
    
    Args:
        schedule_id: ID of the schedule to generate
    
    Returns:
        tuple: (success, message)
    """
    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
        scheduler = TimetableScheduler(schedule)
        return scheduler.generate()
    except Schedule.DoesNotExist:
        return False, f"Schedule with ID {schedule_id} not found"
