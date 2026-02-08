"""
Constraint Validation Module for Timetable Scheduling

This module contains all constraint validation functions used by the scheduling algorithm.
Constraints ensure that the generated timetable is valid and conflict-free.

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from core.models import ScheduleEntry, TimeSlot
from datetime import timedelta


class ConstraintValidator:
    """
    Validates scheduling constraints to ensure timetable integrity.
    
    Constraints checked:
    1. Faculty availability (no double-booking)
    2. Room availability (no double-booking)
    3. Section availability (no double-booking)
    4. Room type matching (Lab courses need Lab rooms)
    5. Maximum continuous hours (max 4 hours for faculty)
    6. Faculty weekly hour limits
    """
    
    def __init__(self, schedule):
        """
        Initialize validator with a schedule.
        
        Args:
            schedule: Schedule object to validate against
        """
        self.schedule = schedule
        self.existing_entries = ScheduleEntry.objects.filter(schedule=schedule)
    
    def validate_faculty_availability(self, teacher, timeslot):
        """
        Check if faculty is available at the given timeslot.
        
        Args:
            teacher: Teacher object
            timeslot: TimeSlot object
        
        Returns:
            tuple: (is_valid, error_message)
        """
        conflict = self.existing_entries.filter(
            teacher=teacher,
            timeslot=timeslot
        ).exists()
        
        if conflict:
            return False, f"Faculty {teacher.teacher_name} is already scheduled at {timeslot}"
        return True, None
    
    def validate_room_availability(self, room, timeslot):
        """
        Check if room is available at the given timeslot.
        
        Args:
            room: Room object
            timeslot: TimeSlot object
        
        Returns:
            tuple: (is_valid, error_message)
        """
        conflict = self.existing_entries.filter(
            room=room,
            timeslot=timeslot
        ).exists()
        
        if conflict:
            return False, f"Room {room.room_id} is already booked at {timeslot}"
        return True, None
    
    def validate_section_availability(self, section, timeslot):
        """
        Check if section is available at the given timeslot.
        
        Args:
            section: Section object
            timeslot: TimeSlot object
        
        Returns:
            tuple: (is_valid, error_message)
        """
        conflict = self.existing_entries.filter(
            section=section,
            timeslot=timeslot
        ).exists()
        
        if conflict:
            return False, f"Section {section.class_id} already has a class at {timeslot}"
        return True, None
    
    def validate_room_type_match(self, course, room):
        """
        Check if room type matches course requirements.
        Lab courses need LAB rooms, theory courses can use any room.
        
        Args:
            course: Course object
            room: Room object
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if course.is_lab and room.room_type != 'LAB':
            return False, f"Lab course {course.course_name} requires a LAB room, but {room.room_id} is a {room.room_type}"
        return True, None
    
    def validate_continuous_hours(self, teacher, timeslot, max_hours=4):
        """
        Check if assigning this slot would exceed maximum continuous teaching hours.
        
        Args:
            teacher: Teacher object
            timeslot: TimeSlot object
            max_hours: Maximum continuous hours allowed (default: 4)
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Get all slots for this teacher on the same day
        same_day_entries = self.existing_entries.filter(
            teacher=teacher,
            timeslot__day=timeslot.day
        ).order_by('timeslot__slot_number')
        
        if not same_day_entries.exists():
            return True, None
        
        # Check continuous hours before and after this slot
        slot_numbers = list(same_day_entries.values_list('timeslot__slot_number', flat=True))
        slot_numbers.append(timeslot.slot_number)
        slot_numbers.sort()
        
        # Find longest continuous sequence
        max_continuous = 1
        current_continuous = 1
        
        for i in range(1, len(slot_numbers)):
            if slot_numbers[i] == slot_numbers[i-1] + 1:
                current_continuous += 1
                max_continuous = max(max_continuous, current_continuous)
            else:
                current_continuous = 1
        
        if max_continuous > max_hours:
            return False, f"Assigning this slot would give {teacher.teacher_name} {max_continuous} continuous hours (max: {max_hours})"
        
        return True, None
    
    def validate_weekly_hours(self, teacher):
        """
        Check if teacher has exceeded weekly hour limit.
        
        Args:
            teacher: Teacher object
        
        Returns:
            tuple: (is_valid, error_message)
        """
        current_hours = self.existing_entries.filter(teacher=teacher).count()
        
        if current_hours >= teacher.max_hours_per_week:
            return False, f"Teacher {teacher.teacher_name} has reached weekly limit of {teacher.max_hours_per_week} hours"
        
        return True, None
    
    def validate_all(self, section, course, teacher, room, timeslot):
        """
        Run all constraint validations for a proposed schedule entry.
        
        Args:
            section: Section object
            course: Course object
            teacher: Teacher object
            room: Room object
            timeslot: TimeSlot object
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check faculty availability
        is_valid, error = self.validate_faculty_availability(teacher, timeslot)
        if not is_valid:
            errors.append(error)
        
        # Check room availability
        is_valid, error = self.validate_room_availability(room, timeslot)
        if not is_valid:
            errors.append(error)
        
        # Check section availability
        is_valid, error = self.validate_section_availability(section, timeslot)
        if not is_valid:
            errors.append(error)
        
        # Check room type match
        is_valid, error = self.validate_room_type_match(course, room)
        if not is_valid:
            errors.append(error)
        
        # Check continuous hours
        is_valid, error = self.validate_continuous_hours(teacher, timeslot)
        if not is_valid:
            errors.append(error)
        
        # Check weekly hours
        is_valid, error = self.validate_weekly_hours(teacher)
        if not is_valid:
            errors.append(error)
        
        return len(errors) == 0, errors


def calculate_schedule_quality(schedule):
    """
    Calculate overall quality score for a schedule (0-100).
    
    Factors considered:
    - Number of conflicts (lower is better)
    - Workload distribution (more balanced is better)
    - Room utilization (higher is better)
    
    Args:
        schedule: Schedule object
    
    Returns:
        float: Quality score (0-100)
    """
    from core.models import ConflictLog
    from django.db.models import Count
    
    score = 100.0
    
    # Penalty for conflicts
    conflict_count = ConflictLog.objects.filter(schedule=schedule, resolved=False).count()
    score -= conflict_count * 5  # -5 points per unresolved conflict
    
    # Check workload distribution
    entries = ScheduleEntry.objects.filter(schedule=schedule)
    if entries.exists():
        teacher_loads = entries.values('teacher').annotate(load=Count('id'))
        loads = [item['load'] for item in teacher_loads]
        if loads:
            avg_load = sum(loads) / len(loads)
            variance = sum((x - avg_load) ** 2 for x in loads) / len(loads)
            # Penalty for high variance (unbalanced workload)
            score -= min(variance * 2, 20)  # Max 20 points penalty
    
    # Ensure score is within bounds
    return max(0.0, min(100.0, score))
