from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .ingestion_utils import parse_classroom_csv, parse_faculty_csv
from .models import Room, Block, Faculty, Department
from django.contrib.auth import get_user_model

User = get_user_model()

class IngestionTests(TestCase):
    def test_parse_classroom_csv(self):
        csv_content = b"""classroom_id,floor_no,room_capacity,room_type
A101,Ground,60,Classroom
C101,Ground,30,Collaborative Lab
"""
        file = SimpleUploadedFile("classrooms.csv", csv_content)
        result = parse_classroom_csv(file)
        
        self.assertEqual(result['created'], 2)
        self.assertTrue(Room.objects.filter(code='A101').exists())
        self.assertTrue(Room.objects.filter(code='C101').exists())
        
        # Check Block inference
        room_a = Room.objects.get(code='A101')
        self.assertEqual(room_a.block.name, 'A')
        self.assertEqual(room_a.room_type, 'LECTURE')
        
        room_c = Room.objects.get(code='C101')
        self.assertEqual(room_c.block.name, 'C')
        self.assertEqual(room_c.room_type, 'LAB')

    def test_parse_faculty_csv(self):
        csv_content = b"""teacher_id,teacher_name,email,department,max_hours_per_week
T001,John Doe,john@test.com,CSE,16
"""
        file = SimpleUploadedFile("faculty.csv", csv_content)
        result = parse_faculty_csv(file)
        
        self.assertEqual(result['created'], 1)
        self.assertTrue(Faculty.objects.filter(name='John Doe').exists())
        
        faculty = Faculty.objects.get(name='John Doe')
        self.assertEqual(faculty.department.code, 'CSE')
        self.assertEqual(faculty.max_weekly_load, 16)
        self.assertEqual(faculty.user.email, 'john@test.com')
