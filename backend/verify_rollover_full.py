import os, sys, django
import requests
import json

# Django Setup
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Schedule, TeacherCourseMapping, Course, Teacher, Room, Section
from django.db import connections

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def run_test():
    log("Starting Full End-to-End Rollover Verification")

    User = get_user_model()
    BASE_URL = 'http://127.0.0.1:8000/api'
    
    # 1. Setup Test User
    username = 'verifier_full'
    password = 'full_password_123'
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email='v@full.com', password=password, role='ADMIN')
    else:
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_superuser = True
        u.is_staff = True
        u.role = 'ADMIN'
        u.save()

    # 2. Setup Data
    log("Setting up test data...")
    t, _ = Teacher.objects.get_or_create(name="Rollover Teacher", employee_id="RT001")
    c, _ = Course.objects.get_or_create(code="ROLL101", name="Rollover Course", credits=4)
    r, _ = Room.objects.get_or_create(name="R-Roll", capacity=60)
    s, _ = Section.objects.get_or_create(name="S-Roll", department="CSE", year=2)
    
    # Create operational data
    if not Schedule.objects.filter(course=c, teacher=t).exists():
        Schedule.objects.create(course=c, teacher=t, room=r, section=s, day_of_week='TUE', start_time='10:00', end_time='11:00')
    if not TeacherCourseMapping.objects.filter(teacher=t, course=c).exists():
        TeacherCourseMapping.objects.create(teacher=t, course=c, section=s)
    
    initial_schedules = Schedule.objects.count()
    initial_mappings = TeacherCourseMapping.objects.count()
    initial_courses = Course.objects.count()
    
    log(f"Initial State: Schedules={initial_schedules}, Mappings={initial_mappings}, Courses={initial_courses}")

    # Close DB connections to allow server to access DB
    connections.close_all()

    # 3. Login
    log("Logging in via API...")
    try:
        resp = requests.post(f'{BASE_URL}/auth/token/', data={'username': username, 'password': password})
        if resp.status_code != 200:
            log(f"Login Failed: {resp.status_code} {resp.text}", "ERROR")
            return
        
        token = resp.json()['access']
        headers = {'Authorization': f'Bearer {token}'}
        
    except requests.exceptions.ConnectionError:
        log("Connection refused. Is the server running?", "ERROR")
        return

    # 4. Trigger Reset
    log("Calling /api/system/reset-semester/ ...")
    resp = requests.post(f'{BASE_URL}/system/reset-semester/', json={'confirmation': 'CONFIRM'}, headers=headers)
    
    if resp.status_code == 200:
        log("API Response: 200 OK")
        log(f"Response: {resp.json()}")
    else:
        log(f"API Failed: {resp.status_code} - {resp.text}", "ERROR")
        return

    # 5. Verify Backup List (via API)
    log("Verifying Backup List...")
    resp = requests.get(f"{BASE_URL}/system/backups/", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        backups = data.get('backups', [])
        if backups:
            latest = backups[0]
            log(f"Top Backup Filename: {latest['filename']}")
            log(f"Top Backup Date: {latest['created_at']}")
            log(f"Top Backup Label: {latest['label']}")
            
            if latest['created_at']:
                log("SUCCESS: Backup date is present.")
            else:
                log("FAILURE: Backup date is missing.", "ERROR")
                
            if latest['label'] == "Pre-Rollover Archive":
                log("SUCCESS: Backup label matches.")
            else:
                log(f"WARNING: Label mismatch. Got '{latest['label']}'", "WARN")
        else:
            log("FAILURE: No backups returned.", "ERROR")
    else:
        log(f"Backup List Failed: {resp.status_code}", "ERROR")

    # 6. Verify Database State (Re-open DB connection or check via API)
    # Checking via API for counts (Admin Dashboard stats)
    log("Verifying Data Deletion via Stats API...")
    # Assuming stats endpoint or just check DB directly since we are local
    # Re-setup Django to check DB
    connections.close_all() # Ensure clean state
    
    final_schedules = Schedule.objects.count()
    final_mappings = TeacherCourseMapping.objects.count()
    final_courses = Course.objects.count()
    
    if final_schedules == 0 and final_mappings == 0:
        log("SUCCESS: Schedules and Mappings are 0.")
    else:
        log(f"FAILURE: Data incorrectly persisted. Schedules={final_schedules}, Mappings={final_mappings}", "ERROR")
        
    if final_courses >= initial_courses:
        log("SUCCESS: Master data preserved.")
    else:
        log(f"FAILURE: Master data lost! Courses={final_courses}", "ERROR")

if __name__ == "__main__":
    run_test()
