"""
Core Data Models for M3 Timetable Scheduling System

This module defines all the core data models for the timetable scheduling system.
Models include: Teacher, Course, Room, TimeSlot, Section, TeacherCourseMapping,
Schedule, ScheduleEntry, Constraint, and ConflictLog.

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Extended user model with roles and department for RBAC.
    
    Attributes:
        role: User role (ADMIN, HOD, FACULTY)
        department: Department code (for HOD/Faculty)
        phone: Contact number
        is_protected: Prevent deletion of critical accounts
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('HOD', 'Head of Department'),
        ('FACULTY', 'Faculty Member'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FACULTY')
    department = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_protected = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'


class AuditLog(models.Model):
    """
    Track critical system changes for accountability.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('LOGIN', 'Logged In'),
        ('LOGOUT', 'Logged Out'),
        ('GENERATE', 'Generated Schedule'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.JSONField(default=dict)  # Store changes or extra info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']


class ChangeRequest(models.Model):
    """
    Track modification requests from HODs that require Admin approval.
    
    HODs can request changes to Teacher data, but these changes must be
    approved by an Admin before being applied to the database.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    CHANGE_TYPE_CHOICES = [
        ('CREATE', 'Create New'),
        ('UPDATE', 'Update Existing'),
        ('DELETE', 'Delete'),
    ]
    
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='change_requests',
        help_text="HOD who submitted this request"
    )
    target_model = models.CharField(
        max_length=50,
        help_text="Model being modified (e.g., 'Teacher')"
    )
    target_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID of the object being modified (null for CREATE)"
    )
    change_type = models.CharField(
        max_length=20, 
        choices=CHANGE_TYPE_CHOICES,
        help_text="Type of change requested"
    )
    proposed_data = models.JSONField(
        help_text="New or modified data in JSON format"
    )
    current_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Current data before change (for UPDATE/DELETE)"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    request_notes = models.TextField(
        blank=True,
        help_text="HOD's explanation for the change"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Admin's notes when reviewing"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='reviewed_requests',
        help_text="Admin who approved/rejected this request"
    )
    
    class Meta:
        db_table = 'change_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.change_type} {self.target_model} by {self.requested_by.username} - {self.status}"





class Teacher(models.Model):
    """
    Represents a faculty member who teaches courses.
    
    Attributes:
        teacher_id: Unique identifier for the teacher (e.g., T001)
        teacher_name: Full name of the teacher
        email: Email address for communication
        department: Department the teacher belongs to (e.g., CSE, ECE)
        max_hours_per_week: Maximum teaching hours allowed per week
    """
    teacher_id = models.CharField(max_length=10, unique=True, primary_key=True)
    teacher_name = models.CharField(max_length=100)
    email = models.EmailField()
    department = models.CharField(max_length=50)
    max_hours_per_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(40)]
    )
    
    class Meta:
        db_table = 'teachers'
        ordering = ['teacher_id']
    
    def __str__(self):
        return f"{self.teacher_id} - {self.teacher_name}"


class Course(models.Model):
    """
    Represents an academic course offered by the institution.
    
    Attributes:
        course_id: Unique course identifier (e.g., 23CSE101)
        course_name: Full name of the course
        year: Year of study (1, 2, 3, or 4)
        semester: Semester type (odd or even)
        lectures: Number of lecture hours per week
        theory: Number of theory hours
        practicals: Number of practical/lab hours
        credits: Credit points for the course
        is_lab: Boolean indicating if it's a lab course
        is_elective: Boolean indicating if it's an elective course
        weekly_slots: Total number of weekly time slots required
    """
    course_id = models.CharField(max_length=20, unique=True, primary_key=True)
    course_name = models.CharField(max_length=200)
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    semester = models.CharField(max_length=10, choices=[('odd', 'Odd'), ('even', 'Even')])
    lectures = models.IntegerField(validators=[MinValueValidator(0)])
    theory = models.IntegerField(validators=[MinValueValidator(0)])
    practicals = models.IntegerField(validators=[MinValueValidator(0)])
    credits = models.IntegerField(validators=[MinValueValidator(0)])
    is_lab = models.BooleanField(default=False)
    is_elective = models.BooleanField(default=False)
    weekly_slots = models.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        db_table = 'courses'
        ordering = ['year', 'semester', 'course_id']
    
    def __str__(self):
        return f"{self.course_id} - {self.course_name}"


class Room(models.Model):
    """
    Represents a physical room/classroom in the institution.
    
    Attributes:
        room_id: Unique room identifier (e.g., A-101)
        block: Building block (A, B, C, etc.)
        floor: Floor number
        room_type: Type of room (CLASSROOM or LAB)
    """
    ROOM_TYPES = [
        ('CLASSROOM', 'Classroom'),
        ('LAB', 'Laboratory'),
    ]
    
    room_id = models.CharField(max_length=20, unique=True, primary_key=True)
    block = models.CharField(max_length=10)
    floor = models.IntegerField(validators=[MinValueValidator(1)])
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    
    class Meta:
        db_table = 'rooms'
        ordering = ['block', 'floor', 'room_id']
    
    def __str__(self):
        return f"{self.room_id} ({self.room_type})"


class TimeSlot(models.Model):
    """
    Represents a time slot in the weekly schedule.
    
    Attributes:
        slot_id: Unique slot identifier (e.g., m1, t2)
        day: Day of the week (MON, TUE, WED, THU, FRI)
        slot_number: Slot number within the day (1-8)
        start_time: Start time of the slot (HH:MM format)
        end_time: End time of the slot (HH:MM format)
    """
    DAYS = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
    ]
    
    slot_id = models.CharField(max_length=10, unique=True, primary_key=True)
    day = models.CharField(max_length=3, choices=DAYS)
    slot_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        db_table = 'timeslots'
        ordering = ['day', 'slot_number']
        unique_together = ['day', 'slot_number']
    
    def __str__(self):
        return f"{self.day} Slot {self.slot_number} ({self.start_time}-{self.end_time})"


class Section(models.Model):
    """
    Represents a class section (group of students).
    
    Attributes:
        class_id: Unique section identifier (e.g., CSE1A)
        year: Year of study
        section: Section letter (A, B, C, etc.)
        department: Department code (CSE, ECE, etc.)
    """
    class_id = models.CharField(max_length=20, unique=True, primary_key=True)
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    section = models.CharField(max_length=5)
    department = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'sections'
        ordering = ['department', 'year', 'section']
    
    def __str__(self):
        return f"{self.class_id} - Year {self.year} Section {self.section}"


class TeacherCourseMapping(models.Model):
    """
    Maps teachers to courses they can teach (many-to-many relationship).
    
    Attributes:
        teacher: Foreign key to Teacher model
        course: Foreign key to Course model
        preference_level: Teacher's preference for teaching this course (1-5)
    """
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_mappings')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='teacher_mappings')
    preference_level = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Low, 5=High preference"
    )
    
    class Meta:
        db_table = 'teacher_course_mapping'
        unique_together = ['teacher', 'course']
    
    def __str__(self):
        return f"{self.teacher.teacher_id} -> {self.course.course_id}"


class Schedule(models.Model):
    """
    Represents a generated timetable schedule.
    
    Attributes:
        schedule_id: Auto-generated unique identifier
        name: Descriptive name for the schedule
        semester: Semester type (odd or even)
        year: Academic year
        status: Current status (PENDING, GENERATING, COMPLETED, FAILED)
        created_at: Timestamp when schedule was created
        completed_at: Timestamp when generation completed
        quality_score: Overall quality score of the schedule (0-100)
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    schedule_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    semester = models.CharField(max_length=10, choices=[('odd', 'Odd'), ('even', 'Even')])
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    quality_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        db_table = 'schedules'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Schedule {self.schedule_id} - {self.name} ({self.status})"


class ScheduleEntry(models.Model):
    """
    Represents a single class assignment in the timetable.
    
    Attributes:
        schedule: Foreign key to Schedule
        section: Foreign key to Section
        course: Foreign key to Course
        teacher: Foreign key to Teacher
        room: Foreign key to Room
        timeslot: Foreign key to TimeSlot
        is_lab_session: Boolean indicating if this is a lab session
    """
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='entries')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    is_lab_session = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'schedule_entries'
        unique_together = [
            ['schedule', 'section', 'timeslot'],  # Section can't have two classes at same time
            ['schedule', 'teacher', 'timeslot'],  # Teacher can't teach two classes at same time
            ['schedule', 'room', 'timeslot'],     # Room can't be used twice at same time
        ]
    
    def __str__(self):
        return f"{self.section.class_id} - {self.course.course_id} @ {self.timeslot.slot_id}"


class Constraint(models.Model):
    """
    Represents scheduling constraints and rules.
    
    Attributes:
        name: Constraint name
        constraint_type: Type of constraint (HARD or SOFT)
        description: Detailed description
        weight: Weight/priority of the constraint (1-10)
        is_active: Whether this constraint is currently active
    """
    CONSTRAINT_TYPES = [
        ('HARD', 'Hard Constraint'),  # Must be satisfied
        ('SOFT', 'Soft Constraint'),  # Preferred but not mandatory
    ]
    
    name = models.CharField(max_length=100, unique=True)
    constraint_type = models.CharField(max_length=10, choices=CONSTRAINT_TYPES)
    description = models.TextField()
    weight = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'constraints'
        ordering = ['-weight', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.constraint_type})"


class ConflictLog(models.Model):
    """
    Logs conflicts detected during schedule generation.
    
    Attributes:
        schedule: Foreign key to Schedule
        conflict_type: Type of conflict detected
        description: Detailed description of the conflict
        severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        detected_at: Timestamp when conflict was detected
        resolved: Whether the conflict has been resolved
    """
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='conflicts')
    conflict_type = models.CharField(max_length=100)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'conflict_logs'
        ordering = ['-detected_at', '-severity']
    
    def __str__(self):
        return f"{self.conflict_type} - {self.severity} ({self.schedule.schedule_id})"
