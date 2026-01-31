from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Access Control
class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('HOD', 'Head of Department'),
        ('FACULTY', 'Faculty'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='FACULTY')
    groups = models.ManyToManyField('auth.Group', related_name='custom_user_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_set', blank=True)

# 2. Infrastructure
class Block(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self): return self.name

class Room(models.Model):
    ROOM_TYPES = (('LECTURE', 'Lecture Hall'), ('LAB', 'Laboratory'))
    code = models.CharField(max_length=20, unique=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    capacity = models.IntegerField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    def __str__(self): return f"{self.code} ({self.room_type})"

# 3. Academic
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    def __str__(self): return self.code

class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    teacher_id = models.CharField(max_length=20, unique=True, null=True, blank=True) # New field
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    max_weekly_load = models.IntegerField(default=12)
    def __str__(self): return self.name

class Course(models.Model):
    COURSE_TYPES = (('CORE', 'Core'), ('ELECTIVE', 'Elective'))
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField(default=1)
    credits = models.IntegerField(default=3)
    lecture_hours = models.IntegerField(default=3)
    tutorial_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='CORE')
    is_lab = models.BooleanField(default=False)
    lab_duration = models.IntegerField(default=0) # Hours per session
    elective_group = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self): return f"{self.code} - {self.name}"

class StudentSection(models.Model):
    section_id = models.CharField(max_length=50, unique=True) # e.g. CSE-1-A
    program = models.CharField(max_length=50) # B.Tech
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField()
    semester_parity = models.CharField(max_length=10) # ODD/EVEN
    section_name = models.CharField(max_length=10) # A, B...
    student_count = models.IntegerField(default=60)
    
    def __str__(self): return self.section_id

class CourseAssignment(models.Model):
    assignment_id = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    section = models.ForeignKey(StudentSection, on_delete=models.CASCADE)
    sessions_per_week = models.IntegerField(default=3)
    duration_per_session = models.IntegerField(default=1) # in hours
    
    def __str__(self): return f"{self.faculty} -> {self.course} ({self.section})"
