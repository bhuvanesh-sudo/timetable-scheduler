"""
URL Configuration for Core App API

This module defines all URL routes for the core app's REST API endpoints.
Uses Django REST Framework's router for automatic URL generation.

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeacherViewSet, CourseViewSet, RoomViewSet,
    TimeSlotViewSet, SectionViewSet, TeacherCourseMappingViewSet,
    ScheduleViewSet, ScheduleEntryViewSet, ConstraintViewSet,
    ConflictLogViewSet, AuditLogViewSet, ChangeRequestViewSet,
    ElectiveAllocationViewSet, DataManagementViewSet
)

from .system_views import (
    list_backups, create_backup, restore_backup, delete_backup, system_info
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'teacher-course-mappings', TeacherCourseMappingViewSet, basename='teacher-course-mapping')
router.register(r'schedules', ScheduleViewSet, basename='schedule')
router.register(r'schedule-entries', ScheduleEntryViewSet, basename='schedule-entry')
router.register(r'constraints', ConstraintViewSet, basename='constraint')
router.register(r'conflict-logs', ConflictLogViewSet, basename='conflict-log')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'change-requests', ChangeRequestViewSet, basename='change-request')
router.register(r'elective-allocations', ElectiveAllocationViewSet, basename='elective-allocation')
router.register(r'data-management', DataManagementViewSet, basename='data-management')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    # System Health & Backup endpoints
    path('system/info/', system_info, name='system-info'),
    path('system/backups/', list_backups, name='list-backups'),
    path('system/backups/create/', create_backup, name='create-backup'),
    path('system/backups/<str:filename>/', delete_backup, name='delete-backup'),
    path('system/restore/<str:filename>/', restore_backup, name='restore-backup'),
]

