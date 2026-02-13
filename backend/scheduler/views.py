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
from core.models import (
    Schedule, ScheduleEntry, Teacher, Room, Section, TimeSlot, Course,
    ElectiveAssignment
)
from core.serializers import ScheduleSerializer, ScheduleDetailSerializer, ElectiveAssignmentSerializer
from .algorithm import generate_schedule
from accounts.permissions import IsHODOrAdmin, IsFacultyOrAbove


from django.core.management import call_command

@api_view(['POST'])
@permission_classes([IsHODOrAdmin])
def trigger_generation(request):
    """
    Trigger schedule generation.
    Clears all existing data (including master data) and re-imports from CSVs
    before generating a new schedule to ensure a fresh start as requested.
    """
    name = request.data.get('name', 'Untitled Schedule')
    semester = request.data.get('semester')
    year = request.data.get('year', 1) # Default year but generation handles all 4
    
    if not semester:
        return Response(
            {"error": "semester is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Step 1: Clear existing schedules and logs
        Schedule.objects.all().delete()
        
        # Step 2: Clear and Reset master data from CSVs
        # This re-imports Teachers, Courses, Rooms, Sections, Mappings
        call_command('import_data', clear=True)
        
        # Step 3: Create fresh schedule object
        schedule = Schedule.objects.create(
            name=name,
            semester=semester,
            year=year,
            status='PENDING'
        )
        
        # Step 4: Generate schedule
        success, message = generate_schedule(schedule.schedule_id)
        
        serializer = ScheduleSerializer(schedule)
        
        return Response({
            "schedule_id": schedule.schedule_id,
            "status": schedule.status,
            "message": message,
            "data": serializer.data
        }, status=status.HTTP_201_CREATED if success else status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            "error": f"Failed to reset and generate: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    
    # Get workload from regular entries
    workload_entries = ScheduleEntry.objects.filter(
        schedule_id=schedule_id,
        teacher__isnull=False
    ).values(
        'teacher__teacher_id',
        'teacher__teacher_name',
        'teacher__max_hours_per_week'
    ).annotate(
        total_hours=Count('id')
    )
    
    # Get workload from elective expansions
    workload_expansions = ElectiveAssignment.objects.filter(
        schedule_id=schedule_id
    ).values(
        'teacher__teacher_id',
        'teacher__teacher_name',
        'teacher__max_hours_per_week'
    ).annotate(
        total_hours=Count('id')
    )
    
    # Combine data
    combined = {}
    for item in workload_entries:
        tid = item['teacher__teacher_id']
        combined[tid] = {
            'teacher_id': tid,
            'teacher_name': item['teacher__teacher_name'],
            'total_hours': item['total_hours'],
            'max_hours': item['teacher__max_hours_per_week']
        }
    
    for item in workload_expansions:
        tid = item['teacher__teacher_id']
        if tid in combined:
            combined[tid]['total_hours'] += item['total_hours']
        else:
            combined[tid] = {
                'teacher_id': tid,
                'teacher_name': item['teacher__teacher_name'],
                'total_hours': item['total_hours'],
                'max_hours': item['teacher__max_hours_per_week']
            }
    
    # Calculate utilization
    result = []
    for tid, data in combined.items():
        utilization = (data['total_hours'] / data['max_hours']) * 100 if data['max_hours'] > 0 else 0
        result.append({
            **data,
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
    
    # Get room usage from regular entries
    room_entries = ScheduleEntry.objects.filter(
        schedule_id=schedule_id,
        room__isnull=False
    ).values(
        'room__room_id',
        'room__room_type'
    ).annotate(
        total_slots_used=Count('id')
    )
    
    # Get room usage from elective expansions
    room_expansions = ElectiveAssignment.objects.filter(
        schedule_id=schedule_id
    ).values(
        'room__room_id',
        'room__room_type'
    ).annotate(
        total_slots_used=Count('id')
    )
    
    # Combine data
    combined = {}
    for item in room_entries:
        rid = item['room__room_id']
        combined[rid] = {
            'room_id': rid,
            'room_type': item['room__room_type'],
            'total_slots_used': item['total_slots_used']
        }
    
    for item in room_expansions:
        rid = item['room__room_id']
        if rid in combined:
            combined[rid]['total_slots_used'] += item['total_slots_used']
        else:
            combined[rid] = {
                'room_id': rid,
                'room_type': item['room__room_type'],
                'total_slots_used': item['total_slots_used']
            }
    
    # Calculate utilization
    result = []
    for rid, data in combined.items():
        utilization = (data['total_slots_used'] / total_slots) * 100
        result.append({
            **data,
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
        
        # Include expansions if this is a bucket
        expansions = []
        if entry.course.is_elective and entry.course.is_schedulable:
            expanded_entries = ElectiveAssignment.objects.filter(parent_entry=entry).select_related('course', 'teacher', 'room')
            for exp in expanded_entries:
                expansions.append({
                    'course_code': exp.course.course_id,
                    'course_name': exp.course.course_name,
                    'teacher_name': exp.teacher.teacher_name if exp.teacher else "N/A",
                    'room': exp.room.room_id if exp.room else "N/A",
                })

        timetable[day][slot_num].append({
            'course_code': entry.course.course_id,
            'course_name': entry.course.course_name,
            'teacher_name': entry.teacher.teacher_name if entry.teacher else "Multiple (Detailed)",
            'room': entry.room.room_id if entry.room else "Multiple (Detailed)",
            'section': entry.section.class_id,
            'is_lab_session': entry.is_lab_session,
            'start_time': entry.timeslot.start_time.strftime('%H:%M'),
            'end_time': entry.timeslot.end_time.strftime('%H:%M'),
            'expansions': expansions
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
            'teacher_name': entry.teacher.teacher_name if entry.teacher else "See Detailed Expansion",
            'room': entry.room.room_id if entry.room else "See Detailed Expansion",
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
    Includes both Core ScheduleEntry and ElectiveAssignment.
    """
    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
    except Schedule.DoesNotExist:
        return Response(
            {"error": "Schedule not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    conflicts = []
    
    # Fetch all entries
    core_entries = list(ScheduleEntry.objects.filter(schedule=schedule).select_related('teacher', 'room', 'section', 'timeslot', 'course'))
    elective_entries = list(ElectiveAssignment.objects.filter(schedule=schedule).select_related('teacher', 'room', 'section', 'timeslot', 'course'))
    
    all_assignments = []
    
    # Normalize entries for checking
    for e in core_entries:
        all_assignments.append({
            'type': 'Core',
            'teacher': e.teacher,
            'room': e.room,
            'section': e.section,
            'timeslot': e.timeslot,
            'course': e.course,
            'is_lab': e.is_lab_session
        })
        
    for e in elective_entries:
        all_assignments.append({
            'type': 'Elective',
            'teacher': e.teacher,
            'room': e.room,
            'section': e.section,
            'timeslot': e.timeslot,
            'course': e.course,
            'is_lab': e.course.is_lab
        })

    # Group by Timeslot for O(N) checking
    from collections import defaultdict
    slots_map = defaultdict(list)
    for idx, item in enumerate(all_assignments):
        slots_map[item['timeslot'].slot_id].append(item)

    # Check Conflicts
    for slot_id, items in slots_map.items():
        # Teachers
        teachers_seen = {}
        # Rooms
        rooms_seen = {}
        # Sections
        sections_seen = {}
        
        for item in items:
            ts = item['timeslot']
            day_slot = f"{ts.day} Slot {ts.slot_number}"
            
            # 1. Teacher Double Booking
            if item['teacher']:
                tid = item['teacher'].teacher_id
                if tid in teachers_seen:
                    prev = teachers_seen[tid]
                    conflicts.append(f"Teacher '{item['teacher'].teacher_name}' double-booked at {day_slot} ({prev['course'].course_name} & {item['course'].course_name})")
                else:
                    teachers_seen[tid] = item

            # 2. Room Double Booking
            if item['room']:
                rid = item['room'].room_id
                if rid in rooms_seen:
                    prev = rooms_seen[rid]
                    conflicts.append(f"Room '{rid}' double-booked at {day_slot} ({prev['course'].course_name} & {item['course'].course_name})")
                else:
                    rooms_seen[rid] = item

            # 3. Section Double Booking (Core vs Elective vs Core)
            # Note: For electives, multiple students from same section might be in different topics?
            # Actually, Section object represents the whole class (e.g., CSE-A).
            # If CSE-A is assigned to Core Course X AND Elective Y at same time -> Conflict.
            # If CSE-A is assigned to Elective Y AND Elective Z at same time -> Conflict (unless it's same bucket?)
            # Wait, ElectiveAssignments for same bucket/slot are fine if they map subsets of students.
            # But here we assume Section is atomic?
            # If 'Section' model implies the whole class, then yes, double booking is bad.
            # EXCEPT if the entries are part of the SAME elective bucket expansion?
            # But ElectiveAssignment splits by section.
            # If Section A has students in Topic 1 and Topic 2 at same time... that implies conflict for the section if we consider section atomic.
            # However, typically electives run in parallel.
            # If Core is scheduled, whole section is busy. If Elective is scheduled, whole section is busy (distributed).
            # So if Core matches Elective -> Conflict.
            if item['section']:
                sid = item['section'].class_id
                if sid in sections_seen:
                    prev = sections_seen[sid]
                    # Allow concurrent electives if they are in the same bucket group?
                    # Or maybe we just verify Core vs Anything.
                    # Verify Core vs Core -> Conflict
                    # Verify Core vs Elective -> Conflict
                    # Verify Elective vs Elective -> Might be valid (Bucket expansion)
                    
                    is_conflict = True
                    if item['type'] == 'Elective' and prev['type'] == 'Elective':
                         # Same bucket?
                         if item['course'].elective_group and prev['course'].elective_group == item['course'].elective_group:
                             is_conflict = False # Parallel electives
                    
                    if is_conflict:
                        conflicts.append(f"Section '{sid}' double-booked at {day_slot} ({prev['course'].course_name} & {item['course'].course_name})")
                else:
                    sections_seen[sid] = item

            # 4. Room Type Mismatch
            if item['room']:
                if item['is_lab']:
                    if item['room'].room_type != 'LAB':
                        conflicts.append(f"Lab '{item['course'].course_name}' in non-lab room '{item['room'].room_id}'")
                else:
                    if item['room'].room_type == 'LAB':
                        conflicts.append(f"Theory '{item['course'].course_name}' in lab room '{item['room'].room_id}'")

    return Response({
        "valid": len(conflicts) == 0,
        "total_entries": len(all_assignments),
        "conflicts": conflicts[:100], # Limit response size
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_elective_assignments(request):
    """
    Get detailed elective assignments for a schedule.
    Returns: List of expanded assignments with Room, Teacher, Course, Section details.
    """
    schedule_id = request.query_params.get('schedule_id')
    if not schedule_id:
        return Response(
            {"error": "schedule_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    assignments = ElectiveAssignment.objects.filter(schedule_id=schedule_id).select_related(
        'course', 'teacher', 'room', 'section', 'timeslot'
    ).order_by('timeslot__day', 'timeslot__slot_number', 'course__course_id')
    
    data = []
    for a in assignments:
        data.append({
            'course_code': a.course.course_id,
            'course_name': a.course.course_name,
            'teacher_name': a.teacher.teacher_name if a.teacher else "N/A",
            'teacher_id': a.teacher.teacher_id if a.teacher else None,
            'room': a.room.room_id if a.room else "N/A",
            'section': a.section.class_id,
            'day': a.timeslot.day,
            'slot': a.timeslot.slot_number,
            'time': f"{a.timeslot.start_time.strftime('%H:%M')} - {a.timeslot.end_time.strftime('%H:%M')}"
        })
        
    return Response(data)
