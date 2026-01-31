import csv
import io
import re
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Block, Room, Department, Faculty, Course, StudentSection, CourseAssignment

User = get_user_model()

def infer_block_from_id(room_id):
    """
    Infers the block name from the first letter of the classroom ID.
    E.g., "A102" -> "A", "C104" -> "C".
    Defaults to "Main" if no letter is found.
    """
    match = re.match(r"([A-Za-z]+)", room_id)
    if match:
        return match.group(1).upper()
    return "Main"

def normalize_room_type(csv_type):
    """
    Maps CSV room types to model choices.
    'Classroom' -> 'LECTURE'
    Everything else -> 'LAB'
    """
    if "Classroom" in csv_type or "Lecture" in csv_type:
        return 'LECTURE'
    return 'LAB'

@transaction.atomic
def parse_classroom_csv(file_obj):
    """
    Parses classroom_v2.csv and updates Room/Block models.
    Expected headers: classroom_id, floor_no, room_capacity, room_type
    """
    decoded_file = file_obj.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)
    
    # Validation: Check headers
    required_cols = {'classroom_id', 'room_capacity', 'room_type'}
    if not required_cols.issubset(reader.fieldnames):
        raise ValueError(f"Invalid CSV. Missing columns: {required_cols - set(reader.fieldnames)}")

    created_count = 0
    updated_count = 0

    for row in reader:
        room_code = row['classroom_id'].strip()
        capacity = int(row['room_capacity'])
        raw_type = row['room_type']
        
        block_name = infer_block_from_id(room_code)
        block, _ = Block.objects.get_or_create(name=block_name)
        
        room_type = normalize_room_type(raw_type)
        
        # Create or Update Room
        room, created = Room.objects.update_or_create(
            code=room_code,
            defaults={
                'block': block,
                'capacity': capacity,
                'room_type': room_type
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
            
    return {"created": created_count, "updated": updated_count}

@transaction.atomic
def parse_faculty_csv(file_obj):
    """
    Parses teachers_updated.csv and updates Faculty/User/Department models.
    Expected headers: teacher_id, teacher_name, email, department, max_hours_per_week
    """
    decoded_file = file_obj.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)
    
    # Validation
    required_cols = {'teacher_id', 'teacher_name', 'email', 'department', 'max_hours_per_week'}
    if not required_cols.issubset(reader.fieldnames):
         raise ValueError(f"Invalid CSV. Missing columns: {required_cols - set(reader.fieldnames)}")

    created_count = 0
    updated_count = 0

    for row in reader:
        tid = row['teacher_id'].strip()
        name = row['teacher_name'].strip()
        email = row['email'].strip()
        dept_code = row['department'].strip()
        max_load = int(row['max_hours_per_week'])
        
        # 1. Department
        department, _ = Department.objects.get_or_create(code=dept_code, defaults={'name': dept_code})
        
        # 2. User Account (Idempotent)
        user, user_created = User.objects.get_or_create(
            username=email, # Use email as username
            defaults={
                'email': email,
                'first_name': name,
                'role': 'FACULTY'
            }
        )
        if user_created:
            user.set_password('welcome123') 
            user.save()
            
        # 3. Faculty Profile
        faculty, created = Faculty.objects.update_or_create(
            teacher_id=tid,
            defaults={
                'user': user,
                'name': name,
                'department': department,
                'max_weekly_load': max_load
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
            
    return {"created": created_count, "updated": updated_count}

@transaction.atomic
def parse_course_csv(file_obj):
    """
    Parses CSE_Courses.csv
    Headers: course_id,course_name,semester,lecture_hours,tutorial_hours,practical_hours,credits,course_type,is_lab,lab_duration,elective_group
    """
    decoded_file = file_obj.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)
    created_count = 0; updated_count = 0
    
    for row in reader:
        code = row['course_id'].strip()
        # Department inference: Assume first 2 chars or default to 'CSE' if not parsing prefix
        # We can hardcode CSE for now as per filename, or if course code is 23CSE...
        dept_code = 'CSE' 
        department, _ = Department.objects.get_or_create(code=dept_code, defaults={'name': dept_code})

        defaults = {
            'name': row['course_name'].strip(),
            'department': department,
            'semester': int(row['semester']),
            'lecture_hours': int(row['lecture_hours']),
            'tutorial_hours': int(row['tutorial_hours']),
            'practical_hours': int(row['practical_hours']),
            'credits': int(row['credits']),
            'course_type': row['course_type'].strip(),
            'is_lab': bool(int(row['is_lab'])),
            'lab_duration': int(row['lab_duration']),
            'elective_group': row['elective_group'].strip() if row['elective_group'] else None
        }

        course, created = Course.objects.update_or_create(code=code, defaults=defaults)
        if created: created_count += 1
        else: updated_count += 1

    return {"created": created_count, "updated": updated_count}

@transaction.atomic
def parse_section_csv(file_obj):
    """
    Parses sections.csv
    Headers: section_id,program,department,year,semester_parity,section_name,student_count
    """
    decoded_file = file_obj.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)
    created_count = 0; updated_count = 0
    
    for row in reader:
        dept_code = row['department'].strip()
        department, _ = Department.objects.get_or_create(code=dept_code, defaults={'name': dept_code})
        
        defaults = {
            'program': row['program'],
            'department': department,
            'year': int(row['year']),
            'semester_parity': row['semester_parity'],
            'section_name': row['section_name'],
            'student_count': int(row['student_count'])
        }
        
        section, created = StudentSection.objects.update_or_create(
            section_id=row['section_id'].strip(), defaults=defaults
        )
        if created: created_count += 1
        else: updated_count += 1
        
    return {"created": created_count, "updated": updated_count}

@transaction.atomic
def parse_assignment_csv(file_obj):
    """
    Parses assignments (1).csv
    Headers: assignment_id,teacher_id,course_id,section_id,sessions_per_week,duration_per_session
    """
    decoded_file = file_obj.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)
    created_count = 0; updated_count = 0
    
    for row in reader:
        try:
            faculty = Faculty.objects.get(teacher_id=row['teacher_id'].strip())
            course = Course.objects.get(code=row['course_id'].strip())
            section = StudentSection.objects.get(section_id=row['section_id'].strip())
            
            defaults = {
                'faculty': faculty,
                'course': course,
                'section': section,
                'sessions_per_week': int(row['sessions_per_week']),
                'duration_per_session': int(row['duration_per_session']),
            }
            
            # Using assignment_id as unique key
            obj, created = CourseAssignment.objects.update_or_create(
                assignment_id=row['assignment_id'].strip(), defaults=defaults
            )
            if created: created_count += 1
            else: updated_count += 1
        except Exception as e:
            print(f"Skipping assignment {row.get('assignment_id')}: {e}")
            continue

    return {"created": created_count, "updated": updated_count}
