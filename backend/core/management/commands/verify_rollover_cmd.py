from django.core.management.base import BaseCommand
import requests
import sys
from django.contrib.auth import get_user_model
from core.models import Schedule, TeacherCourseMapping, ConflictLog, ChangeRequest, Course, Teacher, Room, Section
from rest_framework_simplejwt.tokens import RefreshToken

class Command(BaseCommand):
    help = 'Verify End-to-End Rollover'

    def handle(self, *args, **options):
        self.stdout.write("Starting End-to-End Rollover Verification")
        User = get_user_model()
        BASE_URL = 'http://127.0.0.1:8000/api'

        # 1. Setup Data
        self.stdout.write("Setting up test data...")
        user, created = User.objects.get_or_create(username='verify_admin', defaults={'email': 'verify@test.com', 'role': 'admin'})
        user.set_password('admin123')
        user.save()

        # Ensure some preserved data exists
        t, _ = Teacher.objects.get_or_create(name="Test Teacher", employee_id="T999")
        c, _ = Course.objects.get_or_create(code="TEST101", name="Test Course", credits=3)
        r, _ = Room.objects.get_or_create(name="R-101", capacity=50)
        s, _ = Section.objects.get_or_create(name="S-A", department="CSE", year=1)
        
        # Ensure some operational data exists (to be deleted)
        Schedule.objects.create(course=c, teacher=t, room=r, section=s, day_of_week='MON', start_time='09:00', end_time='10:00')
        TeacherCourseMapping.objects.create(teacher=t, course=c, section=s)
        
        initial_schedules = Schedule.objects.count()
        initial_mappings = TeacherCourseMapping.objects.count()
        initial_courses = Course.objects.count()
        
        self.stdout.write(f"Initial State: Schedules={initial_schedules}, Mappings={initial_mappings}, Courses={initial_courses}")
        
        if initial_schedules == 0 or initial_mappings == 0:
            self.stdout.write(self.style.ERROR("FAILED: Test data not created properly"))
            return

        # 2. Get API Token
        self.stdout.write("Authenticating API...")
        try:
            token = RefreshToken.for_user(user)
            access_token = str(token.access_token)
            headers = {'Authorization': f'Bearer {access_token}'}
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Authentication failed: {e}"))
            return

        # 3. Call Reset Semester
        self.stdout.write("Calling /api/system/reset-semester/ ...")
        try:
            response = requests.post(
                f"{BASE_URL}/system/reset-semester/",
                json={'confirmation': 'CONFIRM'},
                headers=headers
            )
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("API Response: 200 OK"))
                # self.stdout.write(f"Response Data: {response.json()}")
            else:
                self.stdout.write(self.style.ERROR(f"API Failed: {response.status_code} - {response.text}"))
                return
                
        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR("Could not connect to server. Is 'python manage.py runserver' running?"))
            return

        # 4. Verify Database State
        self.stdout.write("Verifying Database State...")
        final_schedules = Schedule.objects.count()
        final_mappings = TeacherCourseMapping.objects.count()
        final_courses = Course.objects.count()
        
        if final_schedules == 0 and final_mappings == 0:
            self.stdout.write(self.style.SUCCESS("SUCCESS: Schedules and Mappings deleted."))
        else:
            self.stdout.write(self.style.ERROR(f"FAILURE: Data not deleted! Schedules={final_schedules}, Mappings={final_mappings}"))
            
        if final_courses == initial_courses:
            self.stdout.write(self.style.SUCCESS("SUCCESS: Courses (Master Data) preserved."))
        else:
            self.stdout.write(self.style.ERROR(f"FAILURE: Master data modified! Courses={final_courses}"))

        # 5. Verify Backup List
        self.stdout.write("Verifying Backup List...")
        resp = requests.get(f"{BASE_URL}/system/backups/", headers=headers)
        if resp.status_code == 200:
            backups = resp.json()['backups']
            if not backups:
                self.stdout.write(self.style.ERROR("FAILURE: No backups found."))
                return
                
            latest = backups[0]
            self.stdout.write(f"Top Backup File: {latest['filename']}")
            self.stdout.write(f"Top Backup Date: {latest['created_at']}")
            self.stdout.write(f"Top Backup Label: {latest['label']}")
            
            # Check if date is valid
            if latest['created_at']:
                self.stdout.write(self.style.SUCCESS("SUCCESS: Backup created and date parsed correctly."))
            else:
                self.stdout.write(self.style.ERROR("FAILURE: Backup date is missing or null."))
                
            # Check if label is correct
            if latest['label'] == "Pre-Rollover Archive":
                self.stdout.write(self.style.SUCCESS("SUCCESS: Backup label is correct."))
            else:
                self.stdout.write(self.style.WARNING(f"WARNING: Backup label mismatch. Expected 'Pre-Rollover Archive', got '{latest['label']}'"))

        else:
            self.stdout.write(self.style.ERROR("Failed to fetch backups."))
