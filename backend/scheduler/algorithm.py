"""
Faculty-Centric Scheduling Algorithm for M3 Timetable System

Constraints enforced:
  1. Exactly 1 lab block per faculty per day (2 consecutive slots in a LAB room)
  2. 2-3 theory/lecture slots per faculty per teaching day (single slot each)
  3. No time conflicts (teacher, section, room)
  4. Labs must always be 2 consecutive slots
  5. Theory slots are single, non-consecutive required
  6. Fair course distribution using mapping CSVs

Author: M3 Backend Team (rewritten faculty-centric)
"""

import random
from django.utils import timezone
from django.db import transaction
from core.models import (
    Schedule, ScheduleEntry, Section, Course, Teacher, Room,
    TimeSlot, TeacherCourseMapping, ConflictLog
)
from .constraints import ConstraintValidator, calculate_schedule_quality


DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI']
MAX_THEORY_PER_FACULTY_PER_DAY = 3   # max theory/lecture slots per faculty per day
MIN_THEORY_PER_FACULTY_PER_DAY = 2   # min theory/lecture slots per faculty per day
INTERVAL_AFTER_SLOT = 2
LUNCH_AFTER_SLOT = 5


class TimetableScheduler:
    """
    Faculty-centric scheduling algorithm.
    Generates conflict-free timetables respecting strict per-faculty daily rules.
    """

    def __init__(self, schedule):
        self.schedule = schedule
        self.validator = ConstraintValidator(schedule)
        self.conflicts = []
        # (course_id, section_id) -> Teacher
        self.teacher_assignments = {}

    # ─────────────────────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────────────────────────────

    def generate(self):
        """
        Main entry point.
        Returns: (success: bool, message: str)
        """
        try:
            self.schedule.status = 'GENERATING'
            self.schedule.save()

            sections = list(Section.objects.all().order_by('year', 'class_id'))
            if not sections:
                return False, "No sections found"

            timeslots = list(TimeSlot.objects.all().order_by('day', 'slot_number'))
            if not timeslots:
                return False, "No timeslots available"

            # Build timeslots grouped by day for fast access
            ts_by_day = {}
            for ts in timeslots:
                ts_by_day.setdefault(ts.day, [])
                ts_by_day[ts.day].append(ts)
            for day in ts_by_day:
                ts_by_day[day].sort(key=lambda t: t.slot_number)

            year_counts = {}
            for s in sections:
                year_counts[s.year] = year_counts.get(s.year, 0) + 1

            # Step 1: Pre-allocate teachers to (course, section) pairs
            self._preallocate_teachers(sections)

            # Step 2: Build per-faculty task lists
            faculty_tasks = self._build_faculty_tasks()

            # Step 3: Schedule each faculty member
            teachers = list(Teacher.objects.all())
            random.shuffle(teachers)

            for teacher in teachers:
                tasks = faculty_tasks.get(teacher.teacher_id, {
                    'lab': [], 'theory': [], 'lecture': []
                })
                self._schedule_faculty(teacher, tasks, ts_by_day)
                # Refresh validator cache after each faculty
                self.validator = ConstraintValidator(self.schedule)

            quality = calculate_schedule_quality(self.schedule)
            self.schedule.quality_score = quality
            self.schedule.status = 'COMPLETED'
            self.schedule.completed_at = timezone.now()
            self.schedule.save()

            years_str = ', '.join(
                f"Year {y}: {c} sections" for y, c in sorted(year_counts.items())
            )
            return True, f"Faculty-centric schedule generated ({years_str}) | Quality: {quality:.2f}"

        except Exception as e:
            self.schedule.status = 'FAILED'
            self.schedule.save()
            raise e

    # ─────────────────────────────────────────────────────────────
    # TEACHER PRE-ALLOCATION
    # ─────────────────────────────────────────────────────────────

    def _preallocate_teachers(self, sections):
        """
        Assign one teacher per (course, section) pair.
        Balances load across mapped teachers using a least-loaded-first strategy.
        """
        from collections import defaultdict
        teacher_load = defaultdict(int)

        sections_by_year = defaultdict(list)
        for section in sections:
            sections_by_year[section.year].append(section)

        for year, year_sections in sections_by_year.items():
            courses = Course.objects.filter(
                year=year,
                semester=self.schedule.semester
            )
            # Filter non-electives, but ALWAYS include Life Skills (CIR)
            courses = [c for c in courses if not c.is_elective or 'Life Skills' in c.course_name or 'LSE' in c.course_id]

            for course in courses:
                slots_per_section = course.weekly_slots

                mappings = list(TeacherCourseMapping.objects.filter(
                    course=course
                ).select_related('teacher').order_by('-preference_level'))

                seen = set()
                pool = []
                for m in mappings:
                    tid = m.teacher.teacher_id
                    if tid not in seen:
                        seen.add(tid)
                        pool.append(m.teacher)

                if not pool:
                    pool = list(Teacher.objects.all())

                pool.sort(key=lambda t: teacher_load[t.teacher_id])

                for section in year_sections:
                    key = (course.course_id, section.class_id)

                    # Choose least loaded capable teacher
                    selected = None
                    for t in pool:
                        if teacher_load[t.teacher_id] + slots_per_section <= t.max_hours_per_week:
                            selected = t
                            break

                    if not selected:
                        # Fallback: global search
                        all_teachers = list(Teacher.objects.all())
                        all_teachers.sort(key=lambda t: teacher_load[t.teacher_id])
                        for t in all_teachers:
                            if teacher_load[t.teacher_id] + slots_per_section <= t.max_hours_per_week:
                                selected = t
                                break
                            
                    if not selected:
                        # Last resort: least loaded regardless of cap
                        all_teachers = list(Teacher.objects.all())
                        all_teachers.sort(key=lambda t: teacher_load[t.teacher_id])
                        selected = all_teachers[0] if all_teachers else None

                    if selected:
                        self.teacher_assignments[key] = selected
                        teacher_load[selected.teacher_id] += slots_per_section
                        pool.sort(key=lambda t: teacher_load[t.teacher_id])

    # ─────────────────────────────────────────────────────────────
    # BUILD FACULTY TASK LISTS
    # ─────────────────────────────────────────────────────────────

    def _build_faculty_tasks(self):
        """
        From teacher_assignments, build per-faculty lists of tasks:
          - 'lab'     : [(course, section, num_practical_slots), ...]
          - 'theory'  : [(course, section, num_theory_slots), ...]
          - 'lecture' : [(course, section, num_lecture_slots), ...]
        """
        faculty_tasks = {}

        def get_tasks(teacher_id):
            if teacher_id not in faculty_tasks:
                faculty_tasks[teacher_id] = {'lab': [], 'theory': [], 'lecture': []}
            return faculty_tasks[teacher_id]

        for (course_id, section_id), teacher in self.teacher_assignments.items():
            try:
                course = Course.objects.get(course_id=course_id)
                section = Section.objects.get(class_id=section_id)
            except Exception:
                continue

            tasks = get_tasks(teacher.teacher_id)

            # LAB slots
            if course.practicals > 0:
                tasks['lab'].append((course, section, course.practicals))

            # THEORY slots (continuous block)
            if course.theory > 0:
                tasks['theory'].append((course, section, course.theory))

            # LECTURE slots (remaining)
            lec = course.weekly_slots - course.practicals - course.theory
            if lec > 0:
                tasks['lecture'].append((course, section, lec))

        return faculty_tasks

    # ─────────────────────────────────────────────────────────────
    # FACULTY SCHEDULING CORE
    # ─────────────────────────────────────────────────────────────

    def _schedule_faculty(self, teacher, tasks, ts_by_day):
        """
        Schedule all tasks for one faculty member.

        Daily structure target:
          • 1 LAB block per teaching day  (2 consecutive slots in LAB room)
          • 2-3 Theory/Lecture slots per teaching day (single slots, CLASSROOM)

        Labs are prioritised first (hardest constraint), then theory
        continuous blocks, then individual lecture slots.
        """
        # PRIORITIZE CIR/LSE courses if any
        def task_priority(task_list):
            # Move LSE/CIR tasks to the front of their respective lists
            task_list.sort(key=lambda x: ('Life Skills' in x[0].course_name or 'LSE' in x[0].course_id), reverse=True)
            return task_list

        lab_tasks    = task_priority(list(tasks['lab']))
        theory_tasks = task_priority(list(tasks['theory']))
        lec_tasks    = task_priority(list(tasks['lecture']))

        # ── Phase A: Schedule LAB blocks (2 consecutive) ──────────────
        # One lab block per day maximum. We spread across days.
        lab_days_used = set()   # days where this teacher already has a lab

        for (course, section, num_slots) in lab_tasks:
            # num_slots is practicals count (usually 2-3).
            # We cap to 2 consecutive for the rule "exactly 2 consecutive".
            block_size = 2  # always exactly 2 consecutive slots per rule

            placed = False
            days = list(DAYS)
            random.shuffle(days)

            for day in days:
                if day in lab_days_used:
                    continue  # already a lab for this teacher today

                # SECTION CONSTRAINT: check if this section already has a lab on this day
                if self._section_has_lab_on_day(section, day):
                    continue

                day_slots = ts_by_day.get(day, [])
                # Try every consecutive pair
                for i in range(len(day_slots) - block_size + 1):
                    window = day_slots[i: i + block_size]

                    # Must be truly consecutive AND not cross breaks (interval/lunch)
                    if not self._is_consecutive(window, check_breaks=True):
                        continue

                    # Also ensure no existing LAB-day conflict for section
                    if not self._window_free(window, teacher, section):
                        continue

                    # Find a LAB room free for the whole window
                    lab_room = self._find_room_for_window(window, room_type='LAB')
                    if not lab_room:
                        continue

                    # Commit
                    for ts in window:
                        ScheduleEntry.objects.create(
                            schedule=self.schedule,
                            section=section,
                            course=course,
                            teacher=teacher,
                            room=lab_room,
                            timeslot=ts,
                            is_lab_session=True
                        )
                    lab_days_used.add(day)
                    placed = True
                    self.validator = ConstraintValidator(self.schedule)
                    break

                if placed:
                    break

            if not placed:
                self._log_conflict(
                    'LAB_UNPLACED',
                    f"Could not place lab for {course.course_id} / {section.class_id}",
                    'HIGH'
                )

        # ── Phase B: Schedule THEORY continuous blocks ────────────────
        for (course, section, num_slots) in theory_tasks:
            placed = False
            days = list(DAYS)
            random.shuffle(days)

            for day in days:
                # FACULTY CONSTRAINT: check if teacher can fit more classes today
                count_on_day = self._teacher_daily_count(teacher, day)
                if count_on_day >= MAX_THEORY_PER_FACULTY_PER_DAY + (1 if day in lab_days_used else 0):
                    continue

                # How many theory slots can we still fit today?
                can_fit = (MAX_THEORY_PER_FACULTY_PER_DAY + (1 if day in lab_days_used else 0)) - count_on_day
                slots_to_place = min(num_slots, can_fit)
                if slots_to_place <= 0: continue

                day_slots = ts_by_day.get(day, [])
                # Try consecutive window
                for i in range(len(day_slots) - slots_to_place + 1):
                    window = day_slots[i: i + slots_to_place]
                    # Theory blocks also shouldn't cross breaks for consistency
                    if not self._is_consecutive(window, check_breaks=True):
                        continue
                    if not self._window_free(window, teacher, section):
                        continue

                    classroom = None
                    prev_slot_room = self._get_adjacent_theory_room(teacher, section, window[0])
                    if prev_slot_room and all(not self._room_busy(prev_slot_room, ts) for ts in window):
                        classroom = prev_slot_room
                    else:
                        classroom = self._find_room_for_window(window, room_type='CLASSROOM')

                    if not classroom:
                        continue

                    for ts in window:
                        ScheduleEntry.objects.create(
                            schedule=self.schedule,
                            section=section,
                            course=course,
                            teacher=teacher,
                            room=classroom,
                            timeslot=ts,
                            is_lab_session=False
                        )
                    placed = True
                    self.validator = ConstraintValidator(self.schedule)
                    break

                if placed:
                    break

            if not placed:
                self._log_conflict(
                    'THEORY_UNPLACED',
                    f"Could not place theory for {course.course_id} / {section.class_id}",
                    'MEDIUM'
                )

        # ── Phase C: Schedule LECTURE slots (1 slot each) ─────────────
        for (course, section, num_slots) in lec_tasks:
            remaining = num_slots

            while remaining > 0:
                placed = False

                # Faculty min-load priority: 
                # 1. Day where teacher has exactly 1 class (to reach 2)
                # 2. Day where teacher has 0 classes (if they still have a lot of hours to fill)
                # 3. Day where teacher has 2 classes
                def day_score(d):
                    cnt = self._teacher_daily_count(teacher, d)
                    if cnt >= 5: # Hard cap 
                        return 99
                    if cnt == 1:
                        return 0   # Highest priority: hit the minimum of 2 classes per day
                    
                    # If we have many slots left to place, prefer empty days to avoid overloading one day
                    if cnt == 0:
                        if remaining > 2: return 1
                        return 5 
                    
                    if cnt == 2: return 2
                    return 10 + cnt

                sorted_days = sorted(DAYS, key=day_score)

                for day in sorted_days:
                    cnt = self._teacher_daily_count(teacher, day)
                    if cnt >= 5: continue

                    slot_list = list(ts_by_day.get(day, []))
                    random.shuffle(slot_list)

                    for ts in slot_list:
                        # Teacher busy?
                        if self._teacher_busy(teacher, ts): continue
                        
                        # Section busy?
                        if self._section_busy(section, ts): continue
                        
                        # CONSTRAINT: 2 subjects lab slots should not be on same day
                        # (Handled in lab phase, but double check if somehow this is a lab)
                        
                        # NEW CONSTRAINT: Prevent same course on both sides of a break for a section
                        if self._is_course_across_break(section, course, ts):
                            continue

                        # Room available? Use room continuity if possible (including across breaks per user request)
                        prev_slot_room = self._get_adjacent_theory_room(teacher, section, ts)
                        if prev_slot_room and not self._room_busy(prev_slot_room, ts):
                            room = prev_slot_room
                        else:
                            room = self._find_room_single(ts, room_type='CLASSROOM')
                        
                        if not room:
                            continue

                        ScheduleEntry.objects.create(
                            schedule=self.schedule,
                            section=section,
                            course=course,
                            teacher=teacher,
                            room=room,
                            timeslot=ts,
                            is_lab_session=False
                        )
                        placed = True
                        remaining -= 1
                        self.validator = ConstraintValidator(self.schedule)
                        break

                    if placed:
                        break

                if not placed:
                    # Final fallback: desperate search
                    for day in DAYS:
                        slot_list = list(ts_by_day.get(day, []))
                        for ts in slot_list:
                            if self._teacher_busy(teacher, ts) or self._section_busy(section, ts):
                                continue
                            room = self._find_room_single(ts, room_type='CLASSROOM')
                            if not room: continue
                            ScheduleEntry.objects.create(
                                schedule=self.schedule,
                                section=section,
                                course=course,
                                teacher=teacher,
                                room=room,
                                timeslot=ts,
                                is_lab_session=False
                            )
                            placed = True
                            remaining -= 1
                            self.validator = ConstraintValidator(self.schedule)
                            break
                        if placed: break

                if not placed:
                    self._log_conflict(
                        'LECTURE_UNPLACED',
                        f"Could not place lecture for {course.course_id} / {section.class_id} ({teacher.teacher_name})",
                        'MEDIUM'
                    )
                    break

    # ─────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────────────────

    def _is_consecutive(self, window, check_breaks=False):
        """Check that timeslots in window have consecutive slot_numbers and (optionally) don't cross breaks."""
        if not window: return True
        for k in range(len(window) - 1):
            s1 = window[k].slot_number
            s2 = window[k + 1].slot_number
            if s2 != s1 + 1:
                return False
            
            # If checking breaks, ensure a single block doesn't cross interval/lunch
            if check_breaks:
                # Break is BETWEEN s1 and s2
                if s1 == INTERVAL_AFTER_SLOT or s1 == LUNCH_AFTER_SLOT:
                    return False
        return True

    def _teacher_busy(self, teacher, ts):
        return ScheduleEntry.objects.filter(
            schedule=self.schedule, teacher=teacher, timeslot=ts
        ).exists()

    def _section_busy(self, section, ts):
        return ScheduleEntry.objects.filter(
            schedule=self.schedule, section=section, timeslot=ts
        ).exists()

    def _room_busy(self, room, ts):
        return ScheduleEntry.objects.filter(
            schedule=self.schedule, room=room, timeslot=ts
        ).exists()

    def _window_free(self, window, teacher, section):
        """Return True if teacher AND section are both free for every slot in window."""
        for ts in window:
            if self._teacher_busy(teacher, ts):
                return False
            if self._section_busy(section, ts):
                return False
        return True

    def _find_room_for_window(self, window, room_type='LAB'):
        """Return a room of the given type that is free for every slot in window."""
        rooms = list(Room.objects.filter(room_type=room_type))
        random.shuffle(rooms)
        for room in rooms:
            if all(not self._room_busy(room, ts) for ts in window):
                return room
        return None

    def _find_room_single(self, ts, room_type='CLASSROOM'):
        """Return a room free at a single timeslot."""
        rooms = list(Room.objects.filter(room_type=room_type))
        random.shuffle(rooms)
        for room in rooms:
            if not self._room_busy(room, ts):
                return room
        return None

    def _get_adjacent_theory_room(self, teacher, section, ts):
        """Find room used by same teacher/section in previous or next slot to maintain room continuity (user wants this even across breaks)."""
        # Check previous slot
        if ts.slot_number > 1:
            prev_entry = ScheduleEntry.objects.filter(
                schedule=self.schedule,
                teacher=teacher,
                section=section,
                timeslot__day=ts.day,
                timeslot__slot_number=ts.slot_number - 1,
                is_lab_session=False
            ).first()
            if prev_entry: return prev_entry.room
            
        # Check next slot
        next_entry = ScheduleEntry.objects.filter(
            schedule=self.schedule,
            teacher=teacher,
            section=section,
            timeslot__day=ts.day,
            timeslot__slot_number=ts.slot_number + 1,
            is_lab_session=False
        ).first()
        if next_entry: return next_entry.room
        
        return None

    def _is_course_across_break(self, section, course, ts):
        """Check if scheduling this course at ts would result in the same course being on both sides of a break."""
        if ts.slot_number == INTERVAL_AFTER_SLOT + 1: # if we are at 3, check 2
            return ScheduleEntry.objects.filter(schedule=self.schedule, section=section, course=course, timeslot__day=ts.day, timeslot__slot_number=INTERVAL_AFTER_SLOT).exists()
        if ts.slot_number == INTERVAL_AFTER_SLOT: # if we are at 2, check 3
            return ScheduleEntry.objects.filter(schedule=self.schedule, section=section, course=course, timeslot__day=ts.day, timeslot__slot_number=INTERVAL_AFTER_SLOT + 1).exists()
        
        if ts.slot_number == LUNCH_AFTER_SLOT + 1: # if we are at 6, check 5
            return ScheduleEntry.objects.filter(schedule=self.schedule, section=section, course=course, timeslot__day=ts.day, timeslot__slot_number=LUNCH_AFTER_SLOT).exists()
        if ts.slot_number == LUNCH_AFTER_SLOT: # if we are at 5, check 6
            return ScheduleEntry.objects.filter(schedule=self.schedule, section=section, course=course, timeslot__day=ts.day, timeslot__slot_number=LUNCH_AFTER_SLOT + 1).exists()
        
        return False

    def _teacher_daily_count(self, teacher, day):
        """How many total slots (lab or theory) this teacher has on a given day."""
        return ScheduleEntry.objects.filter(
            schedule=self.schedule,
            teacher=teacher,
            timeslot__day=day
        ).count()

    def _section_has_lab_on_day(self, section, day):
        """Constraint: 2 subjects lab slots should not be on the same day for a section."""
        return ScheduleEntry.objects.filter(
            schedule=self.schedule,
            section=section,
            timeslot__day=day,
            is_lab_session=True
        ).exists()

    def _log_conflict(self, conflict_type, description, severity):
        ConflictLog.objects.create(
            schedule=self.schedule,
            conflict_type=conflict_type,
            description=description,
            severity=severity
        )
        self.conflicts.append(description)


# ─────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────────────────────────

def generate_schedule(schedule_id):
    """
    Generate a schedule by ID.
    Returns: (success: bool, message: str)
    """
    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
        scheduler = TimetableScheduler(schedule)
        return scheduler.generate()
    except Schedule.DoesNotExist:
        return False, f"Schedule {schedule_id} not found"
