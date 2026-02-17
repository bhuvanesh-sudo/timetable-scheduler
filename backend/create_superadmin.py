import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

User = get_user_model()
username = 'superadmin'
password = 'password123'

user, created = User.objects.get_or_create(username=username, defaults={'email': 'superadmin@example.com'})
if not created:
    user.email = 'superadmin@example.com'
user.set_password(password)
user.role = 'ADMIN'
user.is_superuser = True
user.is_staff = True
user.is_active = True
user.save()

print(f"User {username} {'created' if created else 'updated'}")
print(f"Credentials: {username} / {password}")
