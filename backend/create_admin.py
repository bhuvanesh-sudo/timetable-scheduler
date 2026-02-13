import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'})
    user.set_password('admin123')
    user.role = 'ADMIN'
    user.is_superuser = True
    user.is_staff = True
    user.save()
    if created:
        print("Created new admin user.")
    else:
        print("Updated existing admin user.")
    print("Credentials: username=admin, password=admin123")
except Exception as e:
    print(f"Error: {e}")
