"""
Serializers for M3 Timetable Scheduling System

This module contains DRF serializers for all data models.
Serializers handle conversion between Python objects and JSON for the REST API.

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from rest_framework import serializers
from .models import (
    Teacher, Course, Room, TimeSlot, Section,
    TeacherCourseMapping, Schedule, ScheduleEntry, Constraint, ConflictLog, AuditLog
)


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'timestamp']
        read_only_fields = ['id', 'user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'timestamp']


class TeacherSerializer(serializers.ModelSerializer):
    """
    Serializer for Teacher model.
    Handles CRUD operations for faculty members.
    """
    class Meta:
        model = Teacher
        fields = '__all__'
    
    def validate_max_hours_per_week(self, value):
        """Ensure max hours is reasonable (between 0 and 40)"""
        if value < 0 or value > 40:
            raise serializers.ValidationError("Max hours per week must be between 0 and 40")
        return value


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model.
    Includes validation for course data.
    """
    class Meta:
        model = Course
        fields = '__all__'
    
    def validate(self, data):
        """Validate course data consistency"""
        # Ensure weekly_slots matches the sum of lectures and practicals
        expected_slots = data.get('lectures', 0) + data.get('practicals', 0)
        if data.get('weekly_slots', 0) < expected_slots:
            raise serializers.ValidationError(
                "Weekly slots must be at least the sum of lectures and practicals"
            )
        return data


class RoomSerializer(serializers.ModelSerializer):
    """
    Serializer for Room model.
    Provides room information for timetable assignment.
    """
    class Meta:
        model = Room
        fields = '__all__'


class TimeSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for TimeSlot model.
    Handles time slot data with day and time information.
    """
    class Meta:
        model = TimeSlot
        fields = '__all__'
    
    def validate(self, data):
        """Ensure start time is before end time"""
        if data.get('start_time') >= data.get('end_time'):
            raise serializers.ValidationError("Start time must be before end time")
        return data


class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for Section model.
    Represents class sections/groups of students.
    """
    class Meta:
        model = Section
        fields = '__all__'


class TeacherCourseMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for TeacherCourseMapping model.
    Shows which teachers can teach which courses.
    Includes nested teacher and course details for better readability.
    """
    teacher_name = serializers.CharField(source='teacher.teacher_name', read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    
    class Meta:
        model = TeacherCourseMapping
        fields = ['id', 'teacher', 'teacher_name', 'course', 'course_name', 'preference_level']


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for Schedule model.
    Represents a complete timetable schedule.
    """
    total_entries = serializers.SerializerMethodField()
    total_conflicts = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'schedule_id', 'name', 'semester', 'year', 'status',
            'created_at', 'completed_at', 'quality_score',
            'total_entries', 'total_conflicts'
        ]
        read_only_fields = ['schedule_id', 'created_at', 'completed_at']
    
    def get_total_entries(self, obj):
        """Get total number of schedule entries"""
        return obj.entries.count()
    
    def get_total_conflicts(self, obj):
        """Get total number of unresolved conflicts"""
        return obj.conflicts.filter(resolved=False).count()


class ScheduleEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for ScheduleEntry model.
    Represents individual class assignments in the timetable.
    Includes nested details for better frontend display.
    """
    section_name = serializers.CharField(source='section.class_id', read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    course_code = serializers.CharField(source='course.course_id', read_only=True)
    teacher_name = serializers.CharField(source='teacher.teacher_name', read_only=True)
    room_name = serializers.CharField(source='room.room_id', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    day = serializers.CharField(source='timeslot.day', read_only=True)
    slot_number = serializers.IntegerField(source='timeslot.slot_number', read_only=True)
    start_time = serializers.TimeField(source='timeslot.start_time', read_only=True)
    end_time = serializers.TimeField(source='timeslot.end_time', read_only=True)
    
    class Meta:
        model = ScheduleEntry
        fields = [
            'id', 'schedule', 'section', 'section_name',
            'course', 'course_name', 'course_code',
            'teacher', 'teacher_name',
            'room', 'room_name', 'room_type',
            'timeslot', 'day', 'slot_number', 'start_time', 'end_time',
            'is_lab_session'
        ]


class ConstraintSerializer(serializers.ModelSerializer):
    """
    Serializer for Constraint model.
    Manages scheduling constraints and rules.
    """
    class Meta:
        model = Constraint
        fields = '__all__'


class ConflictLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ConflictLog model.
    Tracks conflicts detected during schedule generation.
    """
    class Meta:
        model = ConflictLog
        fields = '__all__'
        read_only_fields = ['detected_at']


# Detailed serializers for specific use cases

class ScheduleDetailSerializer(serializers.ModelSerializer):
    """
    Detailed schedule serializer with all entries and conflicts.
    Used for viewing complete schedule information.
    """
    entries = ScheduleEntrySerializer(many=True, read_only=True)
    conflicts = ConflictLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Schedule
        fields = [
            'schedule_id', 'name', 'semester', 'year', 'status',
            'created_at', 'completed_at', 'quality_score',
            'entries', 'conflicts'
        ]


class TimetableViewSerializer(serializers.Serializer):
    """
    Custom serializer for timetable view.
    Organizes schedule entries by day and time slot for frontend display.
    """
    day = serializers.CharField()
    slot_number = serializers.IntegerField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    classes = ScheduleEntrySerializer(many=True)
