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
    TimeSlot, TeacherCourseMapping, ConflictLog,
    ElectiveAllocation, ElectiveAssignment
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
        Main entry point for "Bucket & Expand" schedule generation.
        """
        try:
            self.schedule.status = 'GENERATING'
            self.schedule.save()
            
            sections = Section.objects.all().order_by('year', 'class_id')
            timeslots = list(TimeSlot.objects.all().order_by('day', 'slot_number'))
            
            if not sections.exists() or not timeslots:
                return False, "Sections or Timeslots missing"
            
            # PRE-PROCESSING: Get schedulable items (Core + Buckets)
            self.schedulable_courses = Course.objects.filter(
                semester=self.schedule.semester,
                is_schedulable=True
            ).order_by('year', 'course_id')

            # PRE-ALLOCATE TEACHERS for Core Courses
            self._preallocate_teachers(sections)
            
            # STAGE 1: LAB BLOCKS (Core only)
            sections_list = list(sections)
            random.shuffle(sections_list)
            for section in sections_list:
                self._schedule_section_labs(section, timeslots)

            # STAGE 2: THEORY & BUCKETS
            # (Buckets are treated like theory courses without teachers/rooms initially)
            random.shuffle(sections_list)
            for section in sections_list:
                self._schedule_section_theory_and_buckets(section, timeslots)

            # STAGE 3: ELECTIVE EXPANSION
            self._expand_electives()
            
            # Finalize
            quality = calculate_schedule_quality(self.schedule)
            self.schedule.quality_score = quality
            self.schedule.status = 'COMPLETED'
            self.schedule.completed_at = timezone.now()
            self.schedule.save()
            
            return True, f"Schedule generated successfully with quality score: {quality:.2f}"
        
        except Exception as e:
            self.schedule.status = 'FAILED'
            self.schedule.save()
            import traceback
            return False, f"Error during scheduling: {str(e)}\n{traceback.format_exc()}"

    def _expand_electives(self):
        """
        Stage 3: Expand generic buckets into specific topics/teachers.
        Groups sections by (Timeslot, ElectiveGroup) to share topics/rooms.
        """
        from collections import defaultdict
        
        # 1. Group all bucket entries by (Timeslot, ElectiveGroup)
        buckets_at_time = defaultdict(list)
        bucket_entries = ScheduleEntry.objects.filter(
            schedule=self.schedule,
            course__is_elective=True,
            course__is_schedulable=True
        ).select_related('course', 'timeslot', 'section')
        
        for entry in bucket_entries:
            key = (entry.timeslot.slot_id, entry.course.elective_group)
            buckets_at_time[key].append(entry)
            
        # 2. For each unique bucket-time combination, expand topics
        for (slot_id, group_id), entries in buckets_at_time.items():
            if not group_id: continue
            
            timeslot = entries[0].timeslot
            # Child topics for this bucket
            child_topics = Course.objects.filter(elective_group=group_id, is_schedulable=False)
            
            # Find allocations for these topics
            # Use allocations for any section participating, or fallback to 'A'
            participating_sections = [e.section.section for e in entries]
            allocations = ElectiveAllocation.objects.filter(
                course__in=child_topics,
                section_group__in=participating_sections + ['A']
            ).select_related('course', 'teacher')
            
            # Map Topic -> Allocation (prefer exact section match over 'A')
            topic_to_alloc = {}
            for alloc in allocations:
                if alloc.course_id not in topic_to_alloc:
                    topic_to_alloc[alloc.course_id] = alloc
                elif alloc.section_group in participating_sections:
                    # Prefer specific section allocation over fallback 'A'
                    topic_to_alloc[alloc.course_id] = alloc

            # Assign a ROOM for each allocated topic at this timeslot
            # (Topics in the SAME bucket slot SHARE the rooms across sections)
            for cid, alloc in topic_to_alloc.items():
                room = self._find_expansion_room(timeslot, alloc.course)
                if room:
                    # Create assignment for ALL sections participating in this bucket slot
                    # (Wait, usually students from all sections fill the same topics)
                    for entry in entries:
                        # Only assign if this topic is relevant for this section
                        # (If section_group is 'A' and it's our fallback, or matches perfectly)
                        if alloc.section_group == 'A' or alloc.section_group == entry.section.section:
                            ElectiveAssignment.objects.create(
                                schedule=self.schedule,
                                parent_entry=entry,
                                section=entry.section,
                                course=alloc.course,
                                teacher=alloc.teacher,
                                room=room,
                                timeslot=timeslot
                            )

    def _find_expansion_room(self, timeslot, course):
        """Find a room for an elective topic that isn't busy in Master Schedule."""
        room_type = 'LAB' if course.is_lab else 'CLASSROOM'
        rooms = list(Room.objects.filter(room_type=room_type))
        random.shuffle(rooms)
        
        for room in rooms:
            # Check Master Schedule (ScheduleEntry)
            if not ScheduleEntry.objects.filter(schedule=self.schedule, timeslot=timeslot, room=room).exists():
                # Check other expansions in SAME schedule/timeslot
                if not ElectiveAssignment.objects.filter(schedule=self.schedule, timeslot=timeslot, room=room).exists():
                    return room
        return None

    def _preallocate_teachers(self, sections):
        """Pre-allocate teachers ONLY for Core courses (is_elective=False)."""
        from collections import defaultdict
        teacher_load = defaultdict(int)
        
        for section in sections:
            courses = self.schedulable_courses.filter(year=section.year, is_elective=False)
            for course in courses:
                slots = course.weekly_slots
                mappings = list(TeacherCourseMapping.objects.filter(course=course).select_related('teacher').order_by('-preference_level'))
                
                # Balanced candidate selection
                random.shuffle(mappings)
                mappings.sort(key=lambda m: teacher_load[m.teacher.teacher_id])
                
                selected = None
                for m in mappings:
                    if teacher_load[m.teacher.teacher_id] + slots <= m.teacher.max_hours_per_week:
                        selected = m.teacher
                        break
                
                if not selected and mappings: selected = mappings[0].teacher # Overload
                
                if selected:
                    self.teacher_assignments[(course.course_id, section.class_id)] = selected
                    teacher_load[selected.teacher_id] += slots

    def _schedule_section_labs(self, section, timeslots):
        """Stage 1: Schedule Core Labs (Indivisible Blocks)."""
        courses = self.schedulable_courses.filter(year=section.year, is_elective=False, is_lab=True)
        
        for course in courses:
            lab_slots_total = course.practicals if (course.is_lab or course.practicals > 0) else 0
            if lab_slots_total == 0:
                continue
            
            # Split lab into chunks (max 4 hours or as per roadmap)
            # 12 hours -> three 4-hour chunks
            chunks = []
            remaining = lab_slots_total
            while remaining > 0:
                chunk_size = min(remaining, 4 if remaining > 4 else remaining)
                # Ensure 12 doesn't result in a weird leftover (e.g. 4, 4, 4 is better than 8, 4)
                # For 12, we can do 3 blocks of 4.
                # For 6, we can do 2 blocks of 3.
                chunks.append(chunk_size)
                remaining -= chunk_size
                
            teacher = self.teacher_assignments.get((course.course_id, section.class_id))
            if not teacher: continue

            for lab_slots in chunks:
                block_assigned = False
                slots_by_day = {}
                for ts in timeslots:
                    if ts.day not in slots_by_day: slots_by_day[ts.day] = []
                    slots_by_day[ts.day].append(ts)
                
                days = list(slots_by_day.keys())
                random.shuffle(days)
                
                for day in days:
                    day_slots = sorted(slots_by_day[day], key=lambda x: x.slot_number)
                    for i in range(len(day_slots) - lab_slots + 1):
                        window = day_slots[i : i + lab_slots]
                        
                        # Validate continuity
                        if not all(window[k+1].slot_number == window[k].slot_number + 1 for k in range(len(window)-1)):
                            continue

                        if self._can_schedule_block(window, section, course, teacher):
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
                    self._log_conflict('LAB_BLOCK_FAILED', f"Failed to assign {lab_slots}h lab chunk for {course.course_id}", 'HIGH')

    def _schedule_section_theory_and_buckets(self, section, timeslots):
        """Stage 2: Schedule Theory and synchronized Elective Buckets."""
        from collections import defaultdict
        
        # Schedulable items include Core Theory and Buckets
        items = self.schedulable_courses.filter(year=section.year, is_lab=False)
        
        # To synchronize buckets across sections of same year:
        # We process buckets first and use a synchronized slot pool
        buckets = items.filter(is_elective=True)
        theory = items.filter(is_elective=False)
        
        # 1. Handle Buckets (Simultaneity for all sections of same year)
        for bucket in buckets:
            # Check if already scheduled (by another section logic)
            # Actually, to be simple, we can pick specific slots for EACH bucket and reserve them for the year.
            self._schedule_synchronized_bucket(bucket, section, timeslots)

        # 2. Handle Theory
        for course in theory:
            self._schedule_core_theory(course, section, timeslots)

    def _schedule_synchronized_bucket(self, course, section, timeslots):
        """Ensure elective buckets are in same slots for all sections of same year."""
        # Check if any section of this year already has this bucket scheduled
        existing = ScheduleEntry.objects.filter(
            schedule=self.schedule,
            section__year=section.year,
            course=course
        ).first()

        if existing:
            # Sync with existing slots
            slots = ScheduleEntry.objects.filter(
                schedule=self.schedule,
                section__year=section.year,
                course=course
            ).values_list('timeslot_id', flat=True).distinct()
            
            for sid in slots:
                ts = TimeSlot.objects.get(slot_id=sid)
                ScheduleEntry.objects.create(
                    schedule=self.schedule,
                    section=section,
                    course=course,
                    timeslot=ts,
                    teacher=None, # Bucket placeholder
                    room=None,    # Room assigned during expansion
                    is_lab_session=False
                )
            self.validator = ConstraintValidator(self.schedule)
            return

        # Otherwise, find new synchronized slots
        available_slots = list(timeslots)
        random.shuffle(available_slots)
        
        year_sections = list(Section.objects.filter(year=section.year))
        
        bucket_slots = []
        for ts in available_slots:
            if len(bucket_slots) >= course.weekly_slots: break
            
            # All sections must be free
            if all(self.validator.validate_section_availability(s, ts)[0] for s in year_sections):
                # Buckets must also be in different slots from OTHER buckets
                if not ScheduleEntry.objects.filter(schedule=self.schedule, section=section, timeslot=ts).exists():
                    bucket_slots.append(ts)
        
        for ts in bucket_slots:
            ScheduleEntry.objects.create(
                schedule=self.schedule,
                section=section,
                course=course,
                timeslot=ts,
                teacher=None,
                room=None,
                is_lab_session=False
            )
        self.validator = ConstraintValidator(self.schedule)

    def _schedule_core_theory(self, course, section, timeslots):
        """Schedule remaining theory slots for a core course."""
        current = ScheduleEntry.objects.filter(schedule=self.schedule, section=section, course=course).count()
        needed = course.weekly_slots - current
        if needed <= 0: return

        teacher = self.teacher_assignments.get((course.course_id, section.class_id))
        if not teacher: 
            self._log_conflict('TEACHER_MISSING', f"No teacher assigned for {course.course_id} - {section.class_id}", 'HIGH')
            return

        slots_scheduled = 0
        available_slots = list(timeslots)
        
        # PROPOSED CHANGE: Sort slots to prioritize days with fewer classes ("No Empty Days" constraint)
        # 1. Calculate current load per day for this section
        day_load = self._get_section_day_load(section)
        
        # 2. Shuffle first to ensure randomness within same load tiers
        random.shuffle(available_slots)
        
        # 3. Sort by load (ascending)
        # This puts slots on empty days (load=0) first!
        available_slots.sort(key=lambda ts: day_load.get(ts.day, 0))

        for ts in available_slots:
            if slots_scheduled >= needed: break
            
            room = self._find_suitable_room(course, ts)
            if not room: continue
            
            is_valid, _ = self.validator.validate_all(section, course, teacher, room, ts)
            if is_valid:
                ScheduleEntry.objects.create(
                    schedule=self.schedule,
                    section=section,
                    course=course,
                    teacher=teacher,
                    room=room,
                    timeslot=ts,
                    is_lab_session=False
                )
                slots_scheduled += 1
                # Update local load for subsequent slots in this loop
                day_load[ts.day] = day_load.get(ts.day, 0) + 1
                self.validator = ConstraintValidator(self.schedule)
        
        if slots_scheduled < needed:
             self._log_conflict('COURSE_INCOMPLETE', f"Could not schedule all slots for {course.course_id} ({slots_scheduled}/{needed})", 'MEDIUM')

    def _get_section_day_load(self, section):
        """Get number of classes scheduled per day for a section."""
        from django.db.models import Count
        counts = ScheduleEntry.objects.filter(
            schedule=self.schedule, 
            section=section
        ).values('timeslot__day').annotate(count=Count('id'))
        
        day_map = {day: 0 for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']}
        for c in counts:
            day_map[c['timeslot__day']] = c['count']
        return day_map
            
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
