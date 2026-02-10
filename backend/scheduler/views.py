"""
Scheduler API Views

This module provides API endpoints for schedule generation and analytics.

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg
from core.models import Schedule, ScheduleEntry, Teacher, Room, Section, TimeSlot, Course
from core.serializers import ScheduleSerializer, ScheduleDetailSerializer
from .algorithm import generate_schedule
from accounts.permissions import IsHODOrAdmin, IsFacultyOrAbove


@api_view(['POST'])
@permission_classes([IsHODOrAdmin])
def trigger_generation(request):
    """
    Trigger schedule generation.
    """
    name = request.data.get('name', 'Untitled Schedule')
    semester = request.data.get('semester')
    year = request.data.get('year')
    
    if not semester or not year:
        return Response(
            {"error": "semester and year are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create schedule object
    schedule = Schedule.objects.create(
        name=name,
        semester=semester,
        year=year,
        status='PENDING'
    )
    
    # Generate schedule (synchronous for Sprint 1)
    success, message = generate_schedule(schedule.schedule_id)
    
    serializer = ScheduleSerializer(schedule)
    
    return Response({
        "schedule_id": schedule.schedule_id,
        "status": schedule.status,
        "message": message,
        "data": serializer.data
    }, status=status.HTTP_201_CREATED if success else status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsFacultyOrAbove])
def get_workload_analytics(request):
    """
    Get faculty workload analytics.
    """
    schedule_id = request.query_params.get('schedule_id')
    
    if not schedule_id:
        return Response(
            {"error": "schedule_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get workload data
    workload_data = ScheduleEntry.objects.filter(
        schedule_id=schedule_id
    ).values(
        'teacher__teacher_id',
        'teacher__teacher_name',
        'teacher__max_hours_per_week'
    ).annotate(
        total_hours=Count('id')
    )
    
    # Calculate utilization
    result = []
    for item in workload_data:
        utilization = (item['total_hours'] / item['teacher__max_hours_per_week']) * 100
        result.append({
            'teacher_id': item['teacher__teacher_id'],
            'teacher_name': item['teacher__teacher_name'],
            'total_hours': item['total_hours'],
            'max_hours': item['teacher__max_hours_per_week'],
            'utilization': round(utilization, 2)
        })
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsFacultyOrAbove])
def get_room_utilization(request):
    """
    Get room utilization analytics.
    """
    schedule_id = request.query_params.get('schedule_id')
    
    if not schedule_id:
        return Response(
            {"error": "schedule_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Total available slots (40 timeslots per week)
    total_slots = 40
    
    # Get room utilization data
    room_data = ScheduleEntry.objects.filter(
        schedule_id=schedule_id
    ).values(
        'room__room_id',
        'room__room_type'
    ).annotate(
        total_slots_used=Count('id')
    )
    
    # Calculate utilization
    result = []
    for item in room_data:
        utilization = (item['total_slots_used'] / total_slots) * 100
        result.append({
            'room_id': item['room__room_id'],
            'room_type': item['room__room_type'],
            'total_slots_used': item['total_slots_used'],
            'utilization': round(utilization, 2)
        })
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_timetable_view(request):

    """
    Get timetable view for a specific section or teacher.
    
    GET /api/scheduler/timetable?schedule_id=1&section=CSE1A
    GET /api/scheduler/timetable?schedule_id=1&teacher=T001
    
    Returns: Organized timetable data grouped by day and slot
    """
    schedule_id = request.query_params.get('schedule_id')
    section_id = request.query_params.get('section')
    teacher_id = request.query_params.get('teacher')
    
    if not schedule_id:
        return Response(
            {"error": "schedule_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build query
    query = ScheduleEntry.objects.filter(schedule_id=schedule_id)
    
    if section_id:
        query = query.filter(section_id=section_id)
    if teacher_id:
        query = query.filter(teacher_id=teacher_id)
    
    # Get entries with related data
    entries = query.select_related(
        'section', 'course', 'teacher', 'room', 'timeslot'
    ).order_by('timeslot__day', 'timeslot__slot_number')
    
    # Organize by day and slot
    timetable = {}
    for entry in entries:
        day = entry.timeslot.day
        slot_num = entry.timeslot.slot_number
        
        if day not in timetable:
            timetable[day] = {}
        
        if slot_num not in timetable[day]:
            timetable[day][slot_num] = []
        
        timetable[day][slot_num].append({
            'course_code': entry.course.course_id,
            'course_name': entry.course.course_name,
            'teacher_name': entry.teacher.teacher_name,
            'room': entry.room.room_id,
            'section': entry.section.class_id,
            'is_lab_session': entry.is_lab_session,
            'start_time': entry.timeslot.start_time.strftime('%H:%M'),
            'end_time': entry.timeslot.end_time.strftime('%H:%M'),
        })
    
    return Response(timetable)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_schedule(request):
    """
    Get the schedule for the logged-in faculty member.
    Automatically filters by the linked Teacher record.
    """
    user = request.user
    
    # Check if user is linked to a teacher
    if not hasattr(user, 'teacher') or not user.teacher:
        return Response(
            {"error": "No teacher record linked to this account"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    teacher_id = user.teacher.teacher_id
    schedule_id = request.query_params.get('schedule_id')
    
    # If no schedule_id provided, get the most recent completed one
    if not schedule_id:
        latest_schedule = Schedule.objects.filter(status='COMPLETED').order_by('-created_at').first()
        if latest_schedule:
            schedule_id = latest_schedule.schedule_id
            
    if not schedule_id:
        return Response(
            {"error": "No generated schedules found"},
            status=status.HTTP_404_NOT_FOUND
        )
        
    # Reuse the logic from get_timetable_view but force teacher_id
    # We can call the internal logic or just reproduce it here
    
    # Query for the specific schedule and teacher
    entries = ScheduleEntry.objects.filter(
        schedule_id=schedule_id,
        teacher_id=teacher_id
    ).select_related(
        'section', 'course', 'teacher', 'room', 'timeslot'
    ).order_by('timeslot__day', 'timeslot__slot_number')
    
    # Organize by day and slot
    timetable = {}
    for entry in entries:
        day = entry.timeslot.day
        slot_num = entry.timeslot.slot_number
        
        if day not in timetable:
            timetable[day] = {}
        
        if slot_num not in timetable[day]:
            timetable[day][slot_num] = []
        
        timetable[day][slot_num].append({
            'course_code': entry.course.course_id,
            'course_name': entry.course.course_name,
            'teacher_name': entry.teacher.teacher_name,
            'room': entry.room.room_id,
            'section': entry.section.class_id,
            'is_lab_session': entry.is_lab_session,
            'start_time': entry.timeslot.start_time.strftime('%H:%M'),
            'end_time': entry.timeslot.end_time.strftime('%H:%M'),
        })
    
    return Response({
        'schedule_id': schedule_id,
        'timetable': timetable
    })


@api_view(['GET'])
@permission_classes([IsHODOrAdmin])
def validate_schedule(request, schedule_id):
    """
    Run hard-constraint integrity checks on a schedule.
    Checks: Teacher double-booking, Room double-booking,
    Section double-booking, Room-type mismatch.
    """
    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
    except Schedule.DoesNotExist:
        return Response(
            {"error": "Schedule not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    conflicts = []
    entries = ScheduleEntry.objects.filter(schedule=schedule)

    # 1. Teacher double-booking
    teacher_clashes = (
        entries.values('teacher', 'timeslot')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    for c in teacher_clashes:
        t = Teacher.objects.get(pk=c['teacher'])
        ts = TimeSlot.objects.get(pk=c['timeslot'])
        check_count = c['count']
        conflicts.append(
            f"Teacher '{t.teacher_name}' is assigned {check_count} classes at {ts.day} Slot {ts.slot_number}"
        )

    # 2. Room double-booking
    room_clashes = (
        entries.values('room', 'timeslot')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    for c in room_clashes:
        r = Room.objects.get(pk=c['room'])
        ts = TimeSlot.objects.get(pk=c['timeslot'])
        check_count = c['count']
        conflicts.append(
            f"Room '{r.room_id}' has {check_count} classes at {ts.day} Slot {ts.slot_number}"
        )

    # 3. Section double-booking
    section_clashes = (
        entries.values('section', 'timeslot')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    for c in section_clashes:
        s = Section.objects.get(pk=c['section'])
        ts = TimeSlot.objects.get(pk=c['timeslot'])
        check_count = c['count']
        conflicts.append(
            f"Section '{s.class_id}' has {check_count} classes at {ts.day} Slot {ts.slot_number}"
        )

    # 4. Room-type mismatch (lab course in theory room or vice versa)
    for entry in entries.select_related('course', 'room'):
        course = entry.course
        room = entry.room
        if course.is_lab and room.room_type != 'LAB':
            conflicts.append(
                f"Lab course '{course.course_name}' assigned to non-lab room '{room.room_id}'"
            )
        elif not course.is_lab and room.room_type == 'LAB':
            conflicts.append(
                f"Theory course '{course.course_name}' assigned to lab room '{room.room_id}'"
            )

    return Response({
        "valid": len(conflicts) == 0,
        "total_entries": entries.count(),
        "conflicts": conflicts,
    })
