
import os
import django
import sys

# Setup Django
sys.path.append('/Users/Vamsi/Desktop/SE/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import User

def format_logins():
    users = User.objects.all().order_by('role', 'username')
    
    print("| Name | Username | Password | Role | Department |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    
    for u in users:
        password = ""
        if u.is_superuser:
            password = "admin"
        elif u.role == 'HOD':
            password = "hod"
        else:
            password = "faculty"
            
        full_name = f"{u.first_name} {u.last_name}".strip()
        if not full_name:
            full_name = u.username.capitalize()
            
        print(f"| {full_name} | {u.username} | {password} | {u.role} | {u.department} |")

if __name__ == '__main__':
    format_logins()
