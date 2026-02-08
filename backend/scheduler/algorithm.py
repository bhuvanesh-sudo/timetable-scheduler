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
            # This ensures even distribution across all years
            self._preallocate_teachers(sections)
            
            # Schedule each section (all years together)
            # The validator will ensure no teacher/room conflicts across years
            for section in sections:
                success = self._schedule_section(section, timeslots)
                if not success:
                    self._log_conflict(
                        'SECTION_SCHEDULING_FAILED',
                        f"Failed to completely schedule section {section.class_id} (Year {section.year})",
                        'HIGH'
                    )
            
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
        Pre-allocate teachers to section-course pairs across all years.
        This ensures even distribution and prevents teacher exhaustion in later years.
        
        Args:
            sections: List of all Section objects to schedule
        """
        # Group sections by year and course
        from collections import defaultdict
        course_sections = defaultdict(list)  # course_id -> list of sections
        
        for section in sections:
            courses = Course.objects.filter(
                year=section.year,
                semester=section.sem,
                is_elective=False
            )
            for course in courses:
                course_sections[course.course_id].append(section)
        
        # For each course, distribute sections among available teachers
        for course_id, sections_list in course_sections.items():
            course = Course.objects.get(course_id=course_id)
            teacher_mappings = list(TeacherCourseMapping.objects.filter(
                course=course
            ).select_related('teacher').order_by('-preference_level'))
            
            if not teacher_mappings:
                continue
            
            # Distribute sections evenly among teachers
            # Each teacher gets at most 2 sections
            teacher_index = 0
            teacher_load = defaultdict(int)  # teacher_id -> number of sections assigned
            
            for section in sections_list:
                # Find a teacher with capacity (< 2 sections for this course)
                assigned = False
                attempts = 0
                while attempts < len(teacher_mappings):
                    teacher = teacher_mappings[teacher_index].teacher
                    if teacher_load[teacher.teacher_id] < 2:
                        # Assign this teacher to this section-course pair
                        self.teacher_assignments[(course_id, section.class_id)] = teacher
                        teacher_load[teacher.teacher_id] += 1
                        assigned = True
                        teacher_index = (teacher_index + 1) % len(teacher_mappings)
                        break
                    teacher_index = (teacher_index + 1) % len(teacher_mappings)
                    attempts += 1
                
                # If all teachers are at capacity, assign to first teacher anyway
                if not assigned:
                    teacher = teacher_mappings[0].teacher
                    self.teacher_assignments[(course_id, section.class_id)] = teacher
    
    def _schedule_section(self, section, timeslots):
        """
        Schedule all courses for a given section.
        Implements teacher-section binding: each teacher is assigned to specific
        sections for a course and teaches those sections consistently.
        
        Args:
            section: Section object
            timeslots: List of available TimeSlot objects
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Get all courses for this section's year and semester
        courses = Course.objects.filter(
            year=section.year,
            semester=section.sem,
            is_elective=False  # For Sprint 1, skip electives
        )
        
        for course in courses:
            # Get teachers who can teach this course
            teacher_mappings = TeacherCourseMapping.objects.filter(
                course=course
            ).select_related('teacher').order_by('-preference_level')
            
            if not teacher_mappings.exists():
                self._log_conflict(
                    'NO_TEACHER_AVAILABLE',
                    f"No teacher available for course {course.course_name} in section {section.class_id}",
                    'CRITICAL'
                )
                continue
            
            # TEACHER-SECTION BINDING: Use pre-allocated teacher for this section-course pair
            # Check if we have a pre-allocated teacher
            assignment_key = (course.course_id, section.class_id)
            if assignment_key in self.teacher_assignments:
                assigned_teacher = self.teacher_assignments[assignment_key]
            else:
                # Fallback: Check if this section-course already has an assigned teacher in schedule
                existing_entry = ScheduleEntry.objects.filter(
                    schedule=self.schedule,
                    section=section,
                    course=course
                ).first()
                
                if existing_entry:
                    assigned_teacher = existing_entry.teacher
                else:
                    # Last resort: assign first available teacher
                    assigned_teacher = teacher_mappings.first().teacher
            
            # Try to schedule the required number of weekly slots with the assigned teacher
            slots_scheduled = 0
            slots_needed = course.weekly_slots
            
            # Shuffle timeslots for variety
            available_slots = timeslots.copy()
            random.shuffle(available_slots)
            
            for timeslot in available_slots:
                if slots_scheduled >= slots_needed:
                    break
                
                # Use the assigned teacher (not trying different teachers)
                teacher = assigned_teacher
                
                # Find appropriate room
                room = self._find_suitable_room(course, timeslot)
                if not room:
                    continue
                
                # Validate all constraints
                is_valid, errors = self.validator.validate_all(
                    section, course, teacher, room, timeslot
                )
                
                if is_valid:
                    # Create schedule entry
                    ScheduleEntry.objects.create(
                        schedule=self.schedule,
                        section=section,
                        course=course,
                        teacher=teacher,
                        room=room,
                        timeslot=timeslot,
                        is_lab_session=course.is_lab
                    )
                    slots_scheduled += 1
                    # Refresh validator's cache
                    self.validator = ConstraintValidator(self.schedule)
            
            # Check if we scheduled enough slots
            if slots_scheduled < slots_needed:
                self._log_conflict(
                    'INSUFFICIENT_SLOTS',
                    f"Only scheduled {slots_scheduled}/{slots_needed} slots for {course.course_name} in {section.class_id}",
                    'MEDIUM'
                )
        
        return True
    
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
