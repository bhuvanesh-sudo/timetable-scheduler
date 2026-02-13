import os, sys, django
import requests

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Teacher, Course, Schedule

def verify():
    User = get_user_model()
    username = 'verifier_live'
    password = 'live_password_123'

    print("Creating/Updating verifier user...")
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email='v@l.com', password=password, role='ADMIN')
    else:
        u = User.objects.get(username=username)
        u.set_password(password)
        u.role = 'ADMIN'
        u.save()

    # Pre-check: Ensure some data exists to be deleted
    if not Schedule.objects.exists():
        Schedule.objects.create(name="dummy", semester='odd', year=1)

    # Close DB to release locks for Server
    from django.db import connections
    connections.close_all()

    # Live verification
    BASE_URL = 'http://127.0.0.1:8000/api'

    # 1. Login
    print("Logging in...")
    resp = requests.post(f'{BASE_URL}/auth/token/', data={'username': username, 'password': password})
    if resp.status_code != 200:
        print(f"Login Failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    token = resp.json()['access']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Trigger Reset
    print("Triggering reset-semester...")
    resp = requests.post(f'{BASE_URL}/system/reset-semester/', json={'confirmation': 'CONFIRM'}, headers=headers)
    print(f"Reset Status: {resp.status_code}")
    print(f"Reset Content: {resp.text}")

    if resp.status_code == 200:
        print("SUCCESS: Reset triggered.")
    else:
        print("FAILURE")

if __name__ == "__main__":
    verify()
