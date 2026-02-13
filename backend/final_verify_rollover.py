import os
import django
import requests
import time
import sys
from datetime import datetime

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Schedule, TeacherCourseMapping, ConflictLog, ChangeRequest, Course, Teacher, Room, Section
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
BASE_URL = 'http://127.0.0.1:8000/api'

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def run_test():
    log("Starting End-to-End Rollover Verification")

    # 1. Setup Data
    log("Setting up test data...")
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
    
    log(f"Initial State: Schedules={initial_schedules}, Mappings={initial_mappings}, Courses={initial_courses}")
    
    if initial_schedules == 0 or initial_mappings == 0:
        log("FAILED: Test data not created properly", "ERROR")
        return

    # 2. Get API Token
    log("Authenticating API...")
    try:
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        headers = {'Authorization': f'Bearer {access_token}'}
    except Exception as e:
        log(f"Authentication failed: {e}", "ERROR")
        return

    # 3. Call Reset Semester
    log("Calling /api/system/reset-semester/ ...")
    try:
        response = requests.post(
            f"{BASE_URL}/system/reset-semester/",
            json={'confirmation': 'CONFIRM'},
            headers=headers
        )
        
        if response.status_code == 200:
            log("API Response: 200 OK")
            log(f"Response Data: {response.json()}")
        else:
            log(f"API Failed: {response.status_code} - {response.text}", "ERROR")
            return
            
    except requests.exceptions.ConnectionError:
        log("Could not connect to server. Is 'python manage.py runserver' running?", "ERROR")
        return

    # 4. Verify Database State
    log("Verifying Database State...")
    final_schedules = Schedule.objects.count()
    final_mappings = TeacherCourseMapping.objects.count()
    final_courses = Course.objects.count()
    
    if final_schedules == 0 and final_mappings == 0:
        log("SUCCESS: Schedules and Mappings deleted.")
    else:
        log(f"FAILURE: Data not deleted! Schedules={final_schedules}, Mappings={final_mappings}", "ERROR")
        
    if final_courses == initial_courses:
        log("SUCCESS: Courses (Master Data) preserved.")
    else:
        log(f"FAILURE: Master data modified! Courses={final_courses}", "ERROR")

    # 5. Verify Backup List
    log("Verifying Backup List...")
    resp = requests.get(f"{BASE_URL}/system/backups/", headers=headers)
    if resp.status_code == 200:
        backups = resp.json()['backups']
        if not backups:
            log("FAILURE: No backups found.", "ERROR")
            return
            
        latest = backups[0]
        log(f"Top Backup File: {latest['filename']}")
        log(f"Top Backup Date: {latest['created_at']}")
        log(f"Top Backup Label: {latest['label']}")
        
        # Check if date is valid
        if latest['created_at']:
             log("SUCCESS: Backup created and date parsed correctly.")
        else:
             log("FAILURE: Backup date is missing or null.", "ERROR")
             
        # Check if label is correct
        if latest['label'] == "Pre-Rollover Archive":
             log("SUCCESS: Backup label is correct.")
        else:
             log(f"WARNING: Backup label mismatch. Expected 'Pre-Rollover Archive', got '{latest['label']}'", "WARN")

    else:
        log("Failed to fetch backups.", "ERROR")

if __name__ == "__main__":
    run_test()
