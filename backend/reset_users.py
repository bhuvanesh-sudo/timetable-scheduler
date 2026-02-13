
import os
import django
import csv
import random
import re
import sys

# Setup Django
sys.path.append('/Users/Vamsi/Desktop/SE/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import User
from django.contrib.auth import get_user_model

def clean_username(name):
    # Remove initials (e.g., "Aarthi R" -> "Aarthi", "C.Bagavathi" -> "Bagavathi")
    # Also handle multiple names like "Anantha Narayanan V" -> "Anantha"
    
    # Split by common delimiters
    parts = re.split(r'[\s\.]+', name.strip())
    
    # Filter out parts that are likely initials (length 1 or 2 with trailing dot already split)
    # and pick the first substantial name
    clean_parts = [p for p in parts if len(p) > 2]
    
    if not clean_parts:
        # Fallback if all parts are short (unlikely for main names)
        # Just pick the longest part or the first if tied
        clean_parts = sorted(parts, key=len, reverse=True)
    
    username = clean_parts[0].lower()
    return username

def reset_users():
    User = get_user_model()
    
    print("Deleting all existing users...")
    User.objects.all().delete()
    
    # 1. Create Admin
    print("Creating Admin...")
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin'
    )
    admin.role = 'ADMIN'
    admin.save()
    
    # 2. Get Faculty Data from CSVs
    faculty_data = []
    csv_paths = [
        '/Users/Vamsi/Desktop/SE/Datasets/teachers1.csv',
        '/Users/Vamsi/Desktop/SE/Datasets/teachers2.csv'
    ]
    
    for path in csv_paths:
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['teacher_name']:
                    faculty_data.append(row)
    
    print(f"Total faculty found: {len(faculty_data)}")
    
    # Group by department (all are CSE here, but good practice)
    depts = {}
    for f in faculty_data:
        d = f['department']
        if d not in depts: depts[d] = []
        depts[d].append(f)
    
    # Pick HOD per dept
    hod_selections = {}
    for d, members in depts.items():
        hod_selections[d] = random.choice(members)
        print(f"HOD for {d}: {hod_selections[d]['teacher_name']}")
    
    # Track used usernames to avoid duplicates
    used_usernames = {'admin'}
    
    login_info = []
    login_info.append({'Name': 'System Admin', 'Username': 'admin', 'Password': 'admin', 'Role': 'ADMIN', 'Dept': '-'})
    
    # 3. Create Users
    print("Creating Faculty and HOD users...")
    for f in faculty_data:
        full_name = f['teacher_name']
        dept = f['department']
        email = f['email']
        
        base_username = clean_username(full_name)
        username = base_username
        counter = 1
        while username in used_usernames:
            username = f"{base_username}{counter}"
            counter += 1
        
        used_usernames.add(username)
        
        # Check if HOD
        is_hod = (hod_selections[dept]['teacher_id'] == f['teacher_id'])
        role = 'HOD' if is_hod else 'FACULTY'
        password = 'hod' if is_hod else 'faculty'
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.role = role
        user.department = dept
        # Set name fields
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.save()
        
        login_info.append({
            'Name': full_name,
            'Username': username,
            'Password': password,
            'Role': role,
            'Dept': dept
        })
        
    return login_info

if __name__ == '__main__':
    logins = reset_users()
    
    # Print the table info for easy extraction
    print("\n--- LOGIN DATA START ---")
    print("Name | Username | Password | Role | Dept")
    for row in logins:
        print(f"{row['Name']} | {row['Username']} | {row['Password']} | {row['Role']} | {row['Dept']}")
    print("--- LOGIN DATA END ---")
