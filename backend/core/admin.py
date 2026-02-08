from django.contrib import admin
from .models import (
    Teacher, Course, Room, Section, TimeSlot,
    TeacherCourseMapping, Schedule, ScheduleEntry, ConflictLog
)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'teacher_name', 'department', 'max_hours_per_week']
    list_filter = ['department']
    search_fields = ['teacher_name', 'teacher_id']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_id', 'course_name', 'year', 'semester', 'weekly_slots', 'is_lab', 'is_elective']
    list_filter = ['year', 'semester', 'is_lab', 'is_elective']
    search_fields = ['course_name', 'course_id']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_id', 'room_type', 'block', 'floor']
    list_filter = ['room_type', 'block']
    search_fields = ['room_id']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['class_id', 'year', 'section', 'department']
    list_filter = ['year', 'department']
    search_fields = ['class_id']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['slot_id', 'day', 'slot_number', 'start_time', 'end_time']
    list_filter = ['day']

@admin.register(TeacherCourseMapping)
class TeacherCourseMappingAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'course', 'preference_level']
    list_filter = ['preference_level']
    search_fields = ['teacher__teacher_name', 'course__course_name']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['schedule_id', 'name', 'semester', 'year', 'status', 'quality_score', 'created_at']
    list_filter = ['status', 'semester', 'year']
    search_fields = ['name']
    readonly_fields = ['created_at', 'completed_at']

@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'schedule', 'section', 'course', 'teacher', 'room', 'timeslot', 'is_lab_session']
    list_filter = ['is_lab_session', 'schedule']
    search_fields = ['section__class_id', 'course__course_name', 'teacher__teacher_name']
    raw_id_fields = ['schedule', 'section', 'course', 'teacher', 'room', 'timeslot']

@admin.register(ConflictLog)
class ConflictLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'schedule', 'conflict_type', 'severity', 'detected_at']
    list_filter = ['conflict_type', 'severity']
    search_fields = ['description']
    readonly_fields = ['detected_at']


from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'teacher', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Linking', {'fields': ('role', 'teacher', 'department', 'phone', 'is_protected')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Linking', {'fields': ('role', 'teacher', 'department', 'phone', 'is_protected')}),
    )
    search_fields = ['username', 'email', 'teacher__teacher_name']

