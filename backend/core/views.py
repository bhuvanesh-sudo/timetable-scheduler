"""
API Views for M3 Timetable Scheduling System

This module contains all API ViewSets for CRUD operations on core models.
Uses Django REST Framework's ViewSet pattern for clean, RESTful APIs.

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import (
    Teacher, Course, Room, TimeSlot, Section,
    TeacherCourseMapping, Schedule, ScheduleEntry,
    Constraint, ConflictLog, FacultyAvailability, ElectiveBucket
)
from .serializers import (
    TeacherSerializer, CourseSerializer, RoomSerializer,
    TimeSlotSerializer, SectionSerializer, TeacherCourseMappingSerializer,
    ScheduleSerializer, ScheduleDetailSerializer, ScheduleEntrySerializer,
    ConstraintSerializer, ConflictLogSerializer,
    FacultyAvailabilitySerializer, ElectiveBucketSerializer
)
from accounts.permissions import IsAdmin, IsHODOrAdmin, IsFacultyOrAbove


class TeacherViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Teacher CRUD operations.
    """
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(department=user.department)
        return queryset
    
    def get_permissions(self):
        """
        Allow read access to authenticated users, write access to HOD/Admin.
        """
        if self.action in ['list', 'retrieve', 'by_department']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """Get teachers grouped by department"""
        # If HOD, filter by their department automatically? 
        # For now, just trust the query param or show all if Admin
        department = request.query_params.get('department', None)
        if department:
            teachers = Teacher.objects.filter(department=department)
        else:
            teachers = Teacher.objects.all()
        
        serializer = self.get_serializer(teachers, many=True)
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Course CRUD operations.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(department=user.department)
        return queryset
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'by_year', 'by_semester']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Filter courses by year"""
        year = request.query_params.get('year', None)
        if year:
            courses = Course.objects.filter(year=int(year))
        else:
            courses = Course.objects.all()
        
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_semester(self, request):
        """Filter courses by semester"""
        semester = request.query_params.get('semester', None)
        if semester:
            courses = Course.objects.filter(semester=semester)
        else:
            courses = Course.objects.all()
        
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Room CRUD operations.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'by_type']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Filter rooms by type"""
        room_type = request.query_params.get('type', None)
        if room_type:
            rooms = Room.objects.filter(room_type=room_type)
        else:
            rooms = Room.objects.all()
        
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)


class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for TimeSlot (Read-only).
    """
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_day(self, request):
        """Filter time slots by day"""
        day = request.query_params.get('day', None)
        if day:
            slots = TimeSlot.objects.filter(day=day.upper())
        else:
            slots = TimeSlot.objects.all()
        
        serializer = self.get_serializer(slots, many=True)
        return Response(serializer.data)


class SectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Section CRUD operations.
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(department=user.department)
        return queryset
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'by_year']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):

        """Filter sections by year"""
        year = request.query_params.get('year', None)
        if year:
            sections = Section.objects.filter(year=int(year))
        else:
            sections = Section.objects.all()
        
        serializer = self.get_serializer(sections, many=True)
        return Response(serializer.data)


class TeacherCourseMappingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TeacherCourseMapping CRUD operations.
    """
    queryset = TeacherCourseMapping.objects.all()
    serializer_class = TeacherCourseMappingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(
                Q(teacher__department=user.department) | 
                Q(course__department=user.department)
            )
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Schedule operations.
    """
    queryset = Schedule.objects.all()
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return ScheduleDetailSerializer
        return ScheduleSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'entries', 'conflicts']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """Get all schedule entries for a specific schedule"""
        schedule = self.get_object()
        entries = schedule.entries.all()
        serializer = ScheduleEntrySerializer(entries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def conflicts(self, request, pk=None):
        """Get all conflicts for a specific schedule"""
        schedule = self.get_object()
        conflicts = schedule.conflicts.all()
        serializer = ConflictLogSerializer(conflicts, many=True)
        return Response(serializer.data)


class ScheduleEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ScheduleEntry operations.
    """
    queryset = ScheduleEntry.objects.all()
    serializer_class = ScheduleEntrySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(
                Q(teacher__department=user.department) | 
                Q(section__department=user.department) |
                Q(course__department=user.department)
            )
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]


class ConstraintViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Constraint operations.
    """
    queryset = Constraint.objects.all()
    serializer_class = ConstraintSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'active']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active constraints"""
        constraints = Constraint.objects.filter(is_active=True)
        serializer = self.get_serializer(constraints, many=True)
        return Response(serializer.data)


from .models import (
    Teacher, Course, Room, TimeSlot, Section,
    TeacherCourseMapping, Schedule, ScheduleEntry,
    Constraint, ConflictLog, AuditLog
)
from .serializers import (
    TeacherSerializer, CourseSerializer, RoomSerializer,
    TimeSlotSerializer, SectionSerializer, TeacherCourseMappingSerializer,
    ScheduleSerializer, ScheduleDetailSerializer, ScheduleEntrySerializer,
    ConstraintSerializer, ConflictLogSerializer, AuditLogSerializer
)

# ... (existing code)

class ConflictLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for ConflictLog (Read-only).
    """
    queryset = ConflictLog.objects.all()
    serializer_class = ConflictLogSerializer
    permission_classes = [IsHODOrAdmin]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Audit Logs (Read-only).
    Admin/HOD can view logs.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsHODOrAdmin]
    filterset_fields = ['action', 'model_name', 'user']
    search_fields = ['details', 'object_id']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            # Simple filtering for logs related to their department might be complex
            # For now, let's just let them see logs but we could filter by related objects
            return queryset
        return queryset


class FacultyAvailabilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for FacultyAvailability CRUD operations.
    """
    queryset = FacultyAvailability.objects.all()
    serializer_class = FacultyAvailabilitySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(teacher__department=user.department)
        elif user.role == 'FACULTY':
            return queryset.filter(teacher__email=user.email)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsFacultyOrAbove]
        else: # delete, etc
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]


class ElectiveBucketViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ElectiveBucket CRUD operations.
    """
    queryset = ElectiveBucket.objects.all()
    serializer_class = ElectiveBucketSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'HOD' and user.department:
            return queryset.filter(department=user.department)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsHODOrAdmin]
        return [permission() for permission in permission_classes]


class DashboardStatsView(APIView):
    """
    API endpoint for Dashboard Statistics.
    Returns:
        - Total counts (Teachers, Courses, Rooms, Sections)
        - HOD specific stats (Department faculty, sections, pendings)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Base stats
        if user.role == 'HOD' and user.department:
            teachers_q = Teacher.objects.filter(department=user.department)
            courses_q = Course.objects.filter(department=user.department)
            sections_q = Section.objects.filter(department=user.department)
        else:
            teachers_q = Teacher.objects.all()
            courses_q = Course.objects.all()
            sections_q = Section.objects.all()

        stats = {
            "teachers": teachers_q.count(),
            "courses": courses_q.count(),
            "rooms": Room.objects.count(),
            "sections": sections_q.count(),
            "schedules": Schedule.objects.count()
        }

        # HOD Specific Stats
        if user.role == 'HOD' and user.department:
            dept_teachers = teachers_q
            dept_sections = sections_q
            
            # Count pending availabilities
            pending_availabilities = FacultyAvailability.objects.filter(
                teacher__department=user.department,
                status='PENDING'
            ).count()

            # HOD Specific Data Aggregation
            stats['department_stats'] = {
                "department": user.department,
                "total_faculty": dept_teachers.count(),
                "total_sections": dept_sections.count(),
                "pending_constraints": pending_availabilities,
                "faculty_workload": sorted([
                    {
                        "name": t.teacher_name,
                        "id": t.teacher_id,
                        "max_hours": t.max_hours_per_week,
                        "assigned_hours": ScheduleEntry.objects.filter(
                            teacher=t, 
                            schedule__status='COMPLETED'
                        ).count(),
                        # Aggregate specific course/section assignments for detailed audit
                        "assignments": sorted([
                            {
                                "course_id": assignment['course__course_id'],
                                "course_name": assignment['course__course_name'],
                                "section": assignment['section__class_id'],
                                "hours": assignment['count'] # Count of slots = total hours
                            } for assignment in ScheduleEntry.objects.filter(
                                teacher=t,
                                schedule__status='COMPLETED'
                            ).values(
                                'course__course_id', 
                                'course__course_name', 
                                'section__class_id'
                            ).annotate(count=Count('id'))
                        ], key=lambda x: x['course_name'])
                    } for t in dept_teachers
                ], key=lambda x: x['assigned_hours'], reverse=True)
            }

        return Response(stats)
