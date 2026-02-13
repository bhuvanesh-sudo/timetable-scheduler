"""
Django Management Command to Import CSV Data

This command imports all CSV files from the Datasets folder into the database.
It handles teachers, courses, rooms, timeslots, sections, and teacher-course mappings.

Usage: python manage.py import_data

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Teacher, Course, Room, TimeSlot, Section, TeacherCourseMapping, ElectiveAllocation


class Command(BaseCommand):
    help = 'Import data from CSV files in the Datasets folder'
    
    def __init__(self):
        super().__init__()
        # Path to the Datasets folder (two levels up from backend)
        self.datasets_path = os.path.join(
            settings.BASE_DIR.parent, 'Datasets'
        )
    
    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(self.style.SUCCESS('Starting data import...'))
        
        # Clear existing data if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()
        
        # Import data in order (respecting foreign key dependencies)
        try:
            self.import_teachers()
            self.import_courses()
            self.import_rooms()
            self.import_timeslots()
            self.import_sections()
            self.import_teacher_course_mappings()
            self.import_elective_allocations()
            
            self.stdout.write(self.style.SUCCESS('\\n✓ Data import completed successfully!'))
            self.print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\\n✗ Error during import: {str(e)}'))
            raise
    
    def clear_data(self):
        """Clear all existing data from tables"""
        TeacherCourseMapping.objects.all().delete()
        ElectiveAllocation.objects.all().delete()
        Section.objects.all().delete()
        TimeSlot.objects.all().delete()
        Room.objects.all().delete()
        Course.objects.all().delete()
        Teacher.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('  Existing data cleared'))
    
    def import_teachers(self):
        """Import teachers from teachers1.csv and teachers2.csv"""
        self.stdout.write('\\nImporting teachers...')
        count = 0
        
        for filename in ['teachers1.csv', 'teachers2.csv']:
            filepath = os.path.join(self.datasets_path, filename)
            if not os.path.exists(filepath):
                self.stdout.write(self.style.WARNING(f'  File not found: {filename}'))
                continue
            
            with open(filepath, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    Teacher.objects.update_or_create(
                        teacher_id=row['teacher_id'],
                        defaults={
                            'teacher_name': row['teacher_name'],
                            'email': row['email'],
                            'department': row['department'],
                            'max_hours_per_week': int(row['max_hours_per_week']),
                        }
                    )
                    count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} teachers'))
    
    def import_courses(self):
        """Import courses from courses.csv and elective_courses_updated.csv"""
        self.stdout.write('\nImporting courses...')
        count = 0
        
        # 1. Import Core Courses from courses.csv
        core_filepath = os.path.join(self.datasets_path, 'courses.csv')
        if os.path.exists(core_filepath):
            with open(core_filepath, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    Course.objects.update_or_create(
                        course_id=row['course_id'],
                        defaults={
                            'course_name': row['course_name'],
                            'year': int(row['year']),
                            'semester': row['semester'],
                            'lectures': int(row['lectures']),
                            'theory': int(row.get('theory', 0)),
                            'practicals': int(row['practicals']),
                            'credits': int(row['credits']),
                            'is_lab': bool(int(row['is_lab'])),
                            'is_elective': False,
                            'weekly_slots': int(row['weekly_slots']),
                            'is_schedulable': True,
                            'elective_group': None,
                        }
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} core courses'))
        
        # 2. Import Elective Courses from elective_courses_updated.csv
        elective_filepath = os.path.join(self.datasets_path, 'elective_courses_updated.csv')
        elective_count = 0
        if os.path.exists(elective_filepath):
            with open(elective_filepath, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Import ALL courses from this file to ensure we get all 165 records
                    # update_or_create will handle existing courses (from courses.csv) gracefully
                    Course.objects.update_or_create(
                        course_id=row['course_id'],
                        defaults={
                            'course_name': row['course_name'],
                            'year': int(row['year']),
                            'semester': row['semester'],
                            'lectures': int(row['lectures']),
                            'theory': int(row['theory']),
                            'practicals': int(row['practicals']),
                            'credits': int(row['credits']),
                            'is_lab': bool(int(row['is_lab'])),
                            'is_elective': bool(int(row['is_elective'])),
                            'weekly_slots': int(row['weekly_slots']),
                            'is_schedulable': bool(int(row['is_schedulable'])),
                            'elective_group': row['elective_group'] if row['elective_group'] != 'NA' else None,
                        }
                    )
                    elective_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {elective_count} elective courses'))
            
            # Create Bucket Parent Courses
            self._create_elective_buckets()
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Total {Course.objects.count()} courses imported'))

    def _create_elective_buckets(self):
        """
        Auto-generate 'Bucket' courses for elective groups.
        These buckets are schedulable placeholders.
        """
        from django.db.models import Max
        
        # Get all unique elective groups (excluding None or empty)
        groups = Course.objects.exclude(elective_group__isnull=True).exclude(elective_group='').values_list('elective_group', flat=True).distinct()
        
        created_count = 0
        for group in groups:
            if not group or group == 'NA': continue
            
            # Find children to determine slots and year/semester
            children = Course.objects.filter(elective_group=group)
            if not children.exists(): continue
            
            sample = children.first()
            max_slots = children.aggregate(Max('weekly_slots'))['weekly_slots__max'] or 3
            
            # Create/Update Bucket Course
            Course.objects.update_or_create(
                course_id=group,
                defaults={
                    'course_name': f"Elective Bucket ({group})",
                    'year': sample.year,
                    'semester': sample.semester,
                    'lectures': 0,
                    'theory': 0,
                    'practicals': 0,
                    'credits': 0,
                    'is_lab': False,
                    'is_elective': True,
                    'is_schedulable': True, # MUST be schedulable
                    'weekly_slots': max_slots,
                    'elective_group': None # It IS the group, doesn't belong to one
                }
            )
            created_count += 1
            
        self.stdout.write(f"  ✓ Created/Updated {created_count} Elective Bucket courses")
    
    def import_rooms(self):
        """Import rooms from rooms.csv"""
        self.stdout.write('\nImporting rooms...')
        filepath = os.path.join(self.datasets_path, 'rooms.csv')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR('  File not found: rooms.csv'))
            return
        
        count = 0
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Room.objects.update_or_create(
                    room_id=row['room_id'],
                    defaults={
                        'block': row['block'],
                        'floor': int(row['floor']),
                        'room_type': row['room_type'],
                    }
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} rooms'))
    
    def import_timeslots(self):
        """Import timeslots from timeslots.csv"""
        self.stdout.write('\\nImporting timeslots...')
        filepath = os.path.join(self.datasets_path, 'timeslots.csv')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR('  File not found: timeslots.csv'))
            return
        
        count = 0
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Parse time strings (HH:MM format)
                start_time = datetime.strptime(row['start_time'], '%H:%M').time()
                end_time = datetime.strptime(row['end_time'], '%H:%M').time()
                
                TimeSlot.objects.update_or_create(
                    slot_id=row['slot_id'],
                    defaults={
                        'day': row['day'],
                        'slot_number': int(row['slot_number']),
                        'start_time': start_time,
                        'end_time': end_time,
                    }
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} timeslots'))
    
    def import_sections(self):
        """Import sections from classes.csv"""
        self.stdout.write('\\nImporting sections...')
        count = 0
        
        filepath = os.path.join(self.datasets_path, 'classes.csv')
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR('  File not found: classes.csv'))
            return
        
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Section.objects.update_or_create(
                    class_id=row['class_id'],
                    defaults={
                        'year': int(row['year']),
                        'section': row['section'],
                        'department': row['department'],
                    }
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} sections'))
    
    def import_teacher_course_mappings(self):
        """Import teacher-course mappings from mapping1.csv and mapping2.csv"""
        self.stdout.write('\nImporting teacher-course mappings...')
        count = 0
        
        for filename in ['mapping1.csv', 'mapping2.csv']:
            filepath = os.path.join(self.datasets_path, filename)
            if not os.path.exists(filepath):
                self.stdout.write(self.style.WARNING(f'  File not found: {filename}'))
                continue
            
            with open(filepath, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        teacher = Teacher.objects.get(teacher_id=row['teacher_id'])
                        course = Course.objects.get(course_id=row['course_id'])
                        
                        # Default preference level is 3 if not specified
                        preference = int(row.get('preference_level', 3))
                        
                        TeacherCourseMapping.objects.update_or_create(
                            teacher=teacher,
                            course=course,
                            defaults={'preference_level': preference}
                        )
                        count += 1
                    except (Teacher.DoesNotExist, Course.DoesNotExist):
                        # Skip if teacher or course doesn't exist
                        continue
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} mappings'))

    def import_elective_allocations(self):
        """Import elective allocations from elective_allocation.csv"""
        self.stdout.write('\nImporting elective allocations...')
        filepath = os.path.join(self.datasets_path, 'elective_allocation.csv')
        if not os.path.exists(filepath):
            self.stdout.write(self.style.WARNING('  File not found: elective_allocation.csv'))
            return

        count = 0
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    course = Course.objects.get(course_id=row['course_id'])
                    teacher = Teacher.objects.get(teacher_id=row['teacher_id'])
                    
                    ElectiveAllocation.objects.update_or_create(
                        course=course,
                        section_group=row['section_group'],
                        defaults={'teacher': teacher}
                    )
                    count += 1
                except (Course.DoesNotExist, Teacher.DoesNotExist) as e:
                    self.stdout.write(self.style.WARNING(f'  Skipping allocation: {row["course_id"]} -> {row["teacher_id"]} ({str(e)})'))
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} elective allocations'))
    
    def print_summary(self):
        """Print summary of imported data"""
        self.stdout.write('\\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATA IMPORT SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Teachers:                {Teacher.objects.count()}')
        self.stdout.write(f'Courses:                 {Course.objects.count()}')
        self.stdout.write(f'Rooms:                   {Room.objects.count()}')
        self.stdout.write(f'Time Slots:              {TimeSlot.objects.count()}')
        self.stdout.write(f'Sections:                {Section.objects.count()}')
        self.stdout.write(f'Teacher-Course Mappings: {TeacherCourseMapping.objects.count()}')
        self.stdout.write(f'Elective Allocations:    {ElectiveAllocation.objects.count()}')
        self.stdout.write('='*50)
