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
from django.utils import timezone
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
            # Shuffle sections to ensure fairness in resource contention
            sections_list = list(sections)
            random.shuffle(sections_list)
            
            for section in sections_list:
                self._schedule_section_labs(section, timeslots)

            # PHASE 2: THEORY - Schedule Theory for ALL Sections
            # Reshuffle for theory phase
            random.shuffle(sections_list)
            
            for section in sections_list:
                self._schedule_section_theory(section, timeslots)
            
            # Calculate quality score
            quality = calculate_schedule_quality(self.schedule)
            self.schedule.quality_score = quality
            self.schedule.status = 'COMPLETED'
            self.schedule.completed_at = timezone.now()
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
        Pre-allocate teachers with capacity checking (Smart 4+2 Rule).
        """
        from collections import defaultdict
        
        # Track estimated load (hours)
        teacher_load = defaultdict(int) 
        # Note: Ideally we should seed this with existing load if generating partially, 
        # but generation is fresh for this schedule.
        
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
                slots_per_section = course.weekly_slots
                
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
                    # Fallback Strategy: Find any teacher in the same department?
                    # Since Course doesn't have dept, we might infer or just pick ANY available matching dept
                    # For now, let's try to find teachers who teach SIMILAR courses?
                    # Simplest: Find ANY teacher with capacity (Global Fallback)
                    # To be safe, maybe restricted to department if we can guess it.
                    # Given dataset shows mostly "CSE", we'll query all.
                    distinct_teachers = list(Teacher.objects.all())
                    
                    # Logic continues...
                
                # Filter/Sort by available capacity
                # We want teachers who have room for at least 1 section (slots_per_section)
                capable_teachers = []
                overloaded_fallback = [] # Teachers who are full but might need to be used
                
                for t in distinct_teachers:
                    current = teacher_load[t.teacher_id]
                    if current + slots_per_section <= t.max_hours_per_week:
                        capable_teachers.append(t)
                    else:
                        overloaded_fallback.append(t)
                
                # If mapped capable teachers are effectively zero (e.g. all mapped are full)
                # AND we started with mappings (not global), we should Expand Search to Global
                is_mapped_search = (len(distinct_teachers) != Teacher.objects.count()) 
                
                if not capable_teachers and is_mapped_search:
                    # Expand to all teachers with capacity
                    all_teachers = Teacher.objects.all()
                    for t in all_teachers:
                        if t.teacher_id in seen_ids: continue # Already checked
                        current = teacher_load[t.teacher_id]
                        if current + slots_per_section <= t.max_hours_per_week:
                            capable_teachers.append(t)
                
                # Prioritize capable teachers
                # Sort by current utilization (least loaded first) to balance
                capable_teachers.sort(key=lambda t: teacher_load[t.teacher_id])
                
                # If we have enough capable teachers, great.
                # If not, add overloaded ones (sorted by least overloaded)
                overloaded_fallback.sort(key=lambda t: teacher_load[t.teacher_id])
                
                pool = capable_teachers + overloaded_fallback
                
                # Assign to sections via Round Robin but satisfying capacity
                # We need to maintain a pointer or strategy?
                # Simple strategy: Iterate through pool until we find one with capacity.
                # If all full, add to pool from global?
                
                # It's better to fetch ALL capable teachers upfront? 
                # We tried that with fallback.
                # But 'pool' was snapshot.
                
                # Dynamic Assignment Loop
                for i, section in enumerate(year_sections):
                    selected_candidate = None
                    
                    # 1. Try from existing pool (Mapped + Fallback from before)
                    # Sort pool by current load ASC to ensure balancing
                    pool.sort(key=lambda t: teacher_load[t.teacher_id])
                    
                    for cand in pool:
                        if teacher_load[cand.teacher_id] + slots_per_section <= cand.max_hours_per_week:
                            selected_candidate = cand
                            break
                    
                    # 2. If no candidate in pool, Try Global Search (Real-time)
                    if not selected_candidate and is_mapped_search:
                        # Find ANY teacher in system with capacity
                        # Start with same dept if possible (not easy to guess), or just all
                        # Efficiency note: optimize this query
                        # We can iterate through ALL teachers and check `teacher_load`.
                        # Since we have 86 teachers, it's cheap.
                        
                        best_global = None
                        min_load = float('inf')
                        
                        all_teachers = list(Teacher.objects.all())
                        random.shuffle(all_teachers) # Fairness
                        
                        for t in all_teachers:
                            load = teacher_load[t.teacher_id]
                            if load + slots_per_section <= t.max_hours_per_week:
                                if load < min_load:
                                    min_load = load
                                    best_global = t
                                    # Heuristic: if load is 0, pick immediately
                                    if load == 0: break
                        
                        if best_global:
                            selected_candidate = best_global
                            # Add to pool for subsequent iterations of this course? 
                            # Yes, effectively consistent
                            pool.append(selected_candidate)
                    
                    # 3. If still no candidate, we MUST overload someone.
                    if not selected_candidate:
                        # Pick least loaded from pool
                        pool.sort(key=lambda t: teacher_load[t.teacher_id])
                        selected_candidate = pool[0] # Least loaded (even if overloaded)
                    
                    # Execute Assignment
                    self.teacher_assignments[(course.course_id, section.class_id)] = selected_candidate
                    teacher_load[selected_candidate.teacher_id] += slots_per_section


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
            # Check Section availability (validator check_time_conflicts)
            # Check Teacher availability
            # We can use validator.validate_all() but without room (or dummy room)
            # Or manually check basic conflicts
            
            # Simple check using validator internal methods if possible, or validate_all
            # Logic: Teacher free? Section free?
            # We assume Room search comes later
            
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
        Find a suitable CLASSROOM for a theory session at a given timeslot.
        This method is only called from Phase 2 (theory scheduling).
        Lab/practical sessions use _find_block_room instead.
        
        Args:
            course: Course object
            timeslot: TimeSlot object
        
        Returns:
            Room object or None
        """
        # Theory sessions always go in classrooms,
        # regardless of course.is_lab flag.
        # Practical sessions are handled by _find_block_room.
        rooms = list(Room.objects.filter(room_type='CLASSROOM'))
        random.shuffle(rooms)
        
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
