import os
import django
from django.contrib.auth import authenticate, get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

User = get_user_model()
username = 'admin'
password = 'admin123'

print(f"Checking user: {username}")
user_obj = User.objects.filter(username=username).first()

if user_obj:
    print(f"User found: {user_obj.username}")
    print(f"Is Active: {user_obj.is_active}")
    print(f"Is Staff: {user_obj.is_staff}")
    print(f"Is Superuser: {user_obj.is_superuser}")
    print(f"Role: {getattr(user_obj, 'role', 'N/A')}")
    
    auth_user = authenticate(username=username, password=password)
    if auth_user:
        print("Authentication SUCCESSful")
    else:
        print("Authentication FAILED")
else:
    print("User NOT found")

# List all users for debugging
print("\nAll users in database:")
for u in User.objects.all():
    print(f"- {u.username} (Active: {u.is_active}, Role: {getattr(u, 'role', 'N/A')})")
