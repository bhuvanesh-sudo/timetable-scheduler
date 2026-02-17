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

            # STAGE 2: ELECTIVE BUCKETS (Synchronized across sections)
            random.shuffle(sections_list)
            for section in sections_list:
                self._schedule_section_buckets(section, timeslots)

            # STAGE 3: CORE THEORY (Interleaved across courses and sections)
            self._schedule_core_theory_interleaved(sections_list, timeslots)

            # Stage 3: Expansion
            self._expand_electives()
            
            # Post-generation Audit & Diagnostics
            self._audit_final_workload()
            self._report_mapping_mismatches()
            
            # Update status
            self.schedule.status = 'COMPLETED'
            self.schedule.completed_at = timezone.now()
            self.schedule.quality_score = calculate_schedule_quality(self.schedule)
            self.schedule.save()
            
            return True, "Schedule generated successfully"
        
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
        
        sections_shuffled = list(sections)
        random.shuffle(sections_shuffled)
        
        for section in sections_shuffled:
            courses = self.schedulable_courses.filter(year=section.year, is_elective=False)
            for course in courses:
                slots = course.weekly_slots
                mappings = list(TeacherCourseMapping.objects.filter(course=course).select_related('teacher').order_by('-preference_level'))
                
                # Enhanced Balanced candidate selection
                # 1. Prioritize teachers with ZERO load first to hit the 40% target
                # 2. Then sort by current load (Ascending)
                # 3. Then sort by preference level (Descending)
                def get_sort_key(m):
                    load = teacher_load[m.teacher.teacher_id]
                    # If load is below 40% of max, treat as "High Priority"
                    is_underloaded = 1 if load < m.teacher.max_hours_per_week * 0.4 else 2
                    return (is_underloaded, load, -m.preference_level)
                
                mappings.sort(key=get_sort_key)
                
                selected = None
                for m in mappings:
                    # Enforce 95% limit during pre-allocation
                    if teacher_load[m.teacher.teacher_id] + slots <= m.teacher.max_hours_per_week * 0.95:
                        selected = m.teacher
                        break
                
                if not selected:
                    # Log mapping failure
                    if not mappings:
                        self._log_conflict('MISSING_MAPPING', f"No teachers mapped to course {course.course_id}", 'HIGH')
                    else:
                        # STRICT: Do not overload beyond 95%
                        self._log_conflict('OVERLOAD_PREVENTED', f"Could not find available teacher for {course.course_id} in {section.class_id} (All mapped teachers at 95% limit)", 'HIGH')
                
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
            
            # Split lab into chunks
            # If total slots are small (e.g. 12 for Year 4), use smaller chunks to fill 5 days
            chunks = []
            remaining = lab_slots_total
            
            # Target 5 days if total slots >= 5
            if remaining == 12:
                # Force 5 chunks (2+2+2+3+3 = 12) to fill all days
                chunks = [3, 2, 3, 2, 2]
                remaining = 0
            elif remaining >= 5 and remaining <= 15:
                while remaining > 0:
                    csize = 2 if remaining >= 2 else remaining
                    chunks.append(csize)
                    remaining -= csize
            else:
                while remaining > 0:
                    chunk_size = min(remaining, 4 if remaining > 4 else remaining)
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
                
                # Sort days to prioritize those where BOTH section and teacher are empty
                # 1. Get section day load
                sec_day_load = self._get_section_day_load(section)
                # 2. Get teacher day load
                t_day_load = self._get_teacher_day_load(teacher)
                
                def day_sort_key(d):
                    s_load = sec_day_load.get(d, 0)
                    t_load = t_day_load.get(d, 0)
                    # Priority 0: Both empty
                    # Priority 1: Section empty
                    # Priority 2: Teacher empty
                    # Priority 3: Neither empty
                    if s_load == 0 and t_load == 0: p = 0
                    elif s_load == 0: p = 1
                    elif t_load == 0: p = 2
                    else: p = 3
                    return (p, s_load + t_load)

                days = list(slots_by_day.keys())
                days.sort(key=day_sort_key)
                
                for day in days:
                    day_slots = sorted(slots_by_day[day], key=lambda x: x.slot_number)
                    for i in range(len(day_slots) - lab_slots + 1):
                        window = day_slots[i : i + lab_slots]
                        
                        # Validate continuity
                        if not all(window[k+1].slot_number == window[k].slot_number + 1 for k in range(len(window)-1)):
                            continue

                        # Check pre-allocated teacher first
                        teacher = self.teacher_assignments.get((course.course_id, section.class_id))
                        actual_teacher = None
                        fail_reasons = []
                        
                        if teacher:
                             valid, reason = self._can_schedule_block_with_reason(window, section, course, teacher)
                             if valid:
                                 actual_teacher = teacher
                             else:
                                 fail_reasons.append(f"{teacher.teacher_name}: {reason}")
                        
                        if not actual_teacher:
                             # Try fallback from mappings
                             mappings = TeacherCourseMapping.objects.filter(course=course).select_related('teacher').order_by('-preference_level')
                             for m in mappings:
                                 valid, reason = self._can_schedule_block_with_reason(window, section, course, m.teacher)
                                 if valid:
                                     actual_teacher = m.teacher
                                     break
                                 else:
                                     fail_reasons.append(f"{m.teacher.teacher_name}: {reason}")
                                     
                        if actual_teacher:
                             valid_room = self._find_block_room(window, course)
                             if valid_room:
                                 for ts in window:
                                     ScheduleEntry.objects.create(
                                         schedule=self.schedule,
                                         section=section,
                                         course=course,
                                         teacher=actual_teacher,
                                         room=valid_room,
                                         timeslot=ts,
                                         is_lab_session=True
                                     )
                                 block_assigned = True
                                 self.validator = ConstraintValidator(self.schedule)
                                 break
                             else:
                                 fail_reasons.append("No LAB room available in this window")
                    if block_assigned: break
                
                if not block_assigned:
                    self._log_conflict('LAB_BLOCK_FAILED', f"Failed to assign {lab_slots}h lab chunk for {course.course_id}", 'HIGH')

    def _schedule_section_buckets(self, section, timeslots):
        """Stage 2: Schedule synchronized Elective Buckets for a section."""
        # Schedulable items include Buckets
        buckets = self.schedulable_courses.filter(year=section.year, is_elective=True)
        
        for bucket in buckets:
            self._schedule_synchronized_bucket(bucket, section, timeslots)

    def _schedule_core_theory_interleaved(self, sections, timeslots):
        """Stage 3: Schedule Core Theory by interleaving courses across sections."""
        # Get all core courses that are schedulable or have theory components
        all_theory_courses = list(self.schedulable_courses.filter(is_elective=False))
        
        # Sort courses by "difficulty" (higher total demand vs available mappings)
        # For now, just shuffle for randomness
        random.shuffle(all_theory_courses)
        
        for course in all_theory_courses:
            # Shuffle sections so same section doesn't always get priority for different courses
            shuffled_sections = list(sections)
            random.shuffle(shuffled_sections)
            
            for section in shuffled_sections:
                # Check if this course belongs to this section's year/semester
                if course.year == section.year and course.semester == self.schedule.semester:
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
        # 1. Calculate current load per day
        sec_day_load = self._get_section_day_load(section)
        t_day_load = self._get_teacher_day_load(teacher)
        
        # 3. Shuffle first to ensure randomness within same load tiers
        random.shuffle(available_slots)
        
        # 4. Sort by combined load - PRIORITIZE TEACHER VOIDS
        def slot_sort_key(ts):
            s_load = sec_day_load.get(ts.day, 0)
            t_load = t_day_load.get(ts.day, 0)
            
            # Use bits to create hierarchy: Teacher Empty (bit 1), Section Empty (bit 2)
            # We want both empty (00), then Teacher empty (01), then Section empty (10), then full (11)
            if t_load == 0 and s_load == 0: p = 0
            elif t_load == 0: p = 1
            elif s_load == 0: p = 2
            else: p = 3
            
            return (p, t_load, s_load)
            
        available_slots.sort(key=slot_sort_key)

        for ts in available_slots:
            if slots_scheduled >= needed: break
            
            # Simple check for room first to avoid expensive validation
            room = self._find_suitable_room(course, ts)
            if not room: continue
            
            # Reset actual_teacher for each slot
            actual_teacher = None
            
            if teacher:
                is_valid, _ = self.validator.validate_all(section, course, teacher, room, ts)
                if is_valid:
                    actual_teacher = teacher
            
            if not actual_teacher:
                # Try fallback from mappings
                mappings = TeacherCourseMapping.objects.filter(course=course).select_related('teacher').order_by('-preference_level')
                for m in mappings:
                    is_valid, _ = self.validator.validate_all(section, course, m.teacher, room, ts)
                    if is_valid:
                        actual_teacher = m.teacher
                        break

            if actual_teacher:
                ScheduleEntry.objects.create(
                    schedule=self.schedule,
                    section=section,
                    course=course,
                    teacher=actual_teacher,
                    room=room,
                    timeslot=ts,
                    is_lab_session=False
                )
                slots_scheduled += 1
                # Update local load for subsequent slots in this loop
                sec_day_load[ts.day] = sec_day_load.get(ts.day, 0) + 1
                t_day_load[ts.day] = t_day_load.get(ts.day, 0) + 1
                self.validator = ConstraintValidator(self.schedule)
        
        if slots_scheduled < needed:
             # Detailed conflict logging with specific teacher errors
             reasons = []
             teacher_candidates = TeacherCourseMapping.objects.filter(course=course).select_related('teacher')
             for cand in teacher_candidates:
                 # Check why this candidate failed in MOST slots
                 v_all, errors = self.validator.validate_all(section, course, cand.teacher, Room.objects.first(), timeslots[0])
                 if errors:
                     reasons.append(f"{cand.teacher.teacher_name}: {errors[0]}")
             
             final_reason = "; ".join(reasons[:3]) # Limit to top 3
             self._log_conflict('COURSE_INCOMPLETE', f"Could not schedule {needed-slots_scheduled}/{needed} slots for {course.course_id} in {section.class_id} ({final_reason})", 'MEDIUM')

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

    def _get_teacher_day_load(self, teacher):
        """Get number of classes scheduled per day for a teacher."""
        from django.db.models import Count
        if not teacher: return {day: 0 for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']}
        
        # Check both Core and Elective assignments
        core_counts = ScheduleEntry.objects.filter(
            schedule=self.schedule,
            teacher=teacher
        ).values('timeslot__day').annotate(count=Count('id'))
        
        elective_counts = ElectiveAssignment.objects.filter(
            schedule=self.schedule,
            teacher=teacher
        ).values('timeslot__day').annotate(count=Count('id'))
        
        day_map = {day: 0 for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']}
        for c in core_counts:
            day_map[c['timeslot__day']] += c['count']
        for c in elective_counts:
            day_map[c['timeslot__day']] += c['count']
            
        return day_map
            
    
    def _can_schedule_block_with_reason(self, window, section, course, teacher):
        """Check if a block of slots is valid for teacher/section and return reason."""
        for ts in window:
            t_valid, t_msg = self.validator.validate_faculty_availability(teacher, ts)
            if not t_valid: return False, t_msg
            
            s_valid, s_msg = self.validator.validate_section_availability(section, ts)
            if not s_valid: return False, s_msg
            
            c_valid, c_msg = self.validator.validate_continuous_hours(teacher, ts)
            if not c_valid: return False, c_msg
            
            # Check weekly hours for the WHOLE block!
            w_valid, w_msg = self.validator.validate_weekly_hours(teacher, planned_increment=len(window))
            if not w_valid: return False, w_msg
            
        return True, None

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
    
    def _any_room_free(self, timeslot):
        """Check if any classroom is free at a given timeslot."""
        rooms = Room.objects.filter(room_type='CLASSROOM')
        for room in rooms:
            if not ScheduleEntry.objects.filter(schedule=self.schedule, timeslot=timeslot, room=room).exists():
                return True
        return False
    
    def _audit_final_workload(self):
        """Perform post-generation audit of faculty workloads and log distribution issues."""
        teachers = Teacher.objects.all()
        total_capacity = 0
        total_load = 0
        underloaded = []
        
        for t in teachers:
            total_capacity += t.max_hours_per_week
            
            core_count = ScheduleEntry.objects.filter(schedule=self.schedule, teacher=t).count()
            elective_count = ElectiveAssignment.objects.filter(schedule=self.schedule, teacher=t).count()
            current_total = core_count + elective_count
            total_load += current_total
            
            # Check for < 50% load
            if t.max_hours_per_week > 0:
                utilization = (current_total / t.max_hours_per_week)
                if utilization < 0.5:
                    underloaded.append((t.teacher_name, utilization))

        # Check for absolute capacity deficit
        # (Total weekly core slots + estimated elective expansion demand)
        # We already calculated demand diagnostic as 1544 for core only.
        if total_load > total_capacity * 0.95:
             self._log_conflict('CAPACITY_CRITICAL', f"Total system load ({total_load}h) is nearing/exceeding 95% of total capacity ({int(total_capacity*0.95)}h).", 'HIGH')
        
        if underloaded:
            # Sort by most underloaded
            underloaded.sort(key=lambda x: x[1])
            count = len(underloaded)
            summary = ", ".join([f"{name} ({int(util*100)}%)" for name, util in underloaded[:5]])
            self._log_conflict('UNDERLOADED_FACULTY', f"{count} faculty are under 40% utilized. Most underloaded: {summary}", 'LOW')
            
        # Audit Section Continuity
        self._audit_section_continuity()

    def _audit_section_continuity(self):
        """Check if any section has a day with zero classes."""
        sections = Section.objects.all()
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        empty_days = []
        
        for sec in sections:
            for d in days:
                if not ScheduleEntry.objects.filter(schedule=self.schedule, section=sec, timeslot__day=d).exists():
                    empty_days.append(f"{sec.class_id}({d})")
        
        if empty_days:
            summary = ", ".join(empty_days[:5])
            self._log_conflict('EMPTY_DAY_DETECTED', f"{len(empty_days)} section-days have no classes. Examples: {summary}", 'MEDIUM')

    def _report_mapping_mismatches(self):
        """Identify teachers who cannot be assigned due to semester mapping mismatch."""
        teachers = Teacher.objects.all()
        mismatched = []
        for t in teachers:
            # Check if has ANY mappings
            all_maps = TeacherCourseMapping.objects.filter(teacher=t)
            if all_maps.exists():
                # Check if any mapping matches current semester
                sem_maps = all_maps.filter(course__semester=self.schedule.semester)
                if not sem_maps.exists():
                    mismatched.append(t.teacher_name)
        
        if mismatched:
            summary = ", ".join(mismatched[:5])
            self._log_conflict('DATA_MAPPING_GAP', f"{len(mismatched)} faculty have no mappings for semester '{self.schedule.semester}'. Examples: {summary}", 'HIGH')

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
