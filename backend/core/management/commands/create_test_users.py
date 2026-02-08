from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test users for each role (Admin, HOD, Faculty)'

    def handle(self, *args, **kwargs):
        users = [
            # Admin already exists as 'admin', but let's make a clear test one
            {'username': 'test_admin', 'password': 'password123', 'role': 'ADMIN', 'email': 'admin@m3.com', 'dept': 'ADMIN'},
            
            # HODs
            {'username': 'hod_cse', 'password': 'password123', 'role': 'HOD', 'email': 'hod.cse@m3.com', 'dept': 'CSE'},
            {'username': 'hod_ece', 'password': 'password123', 'role': 'HOD', 'email': 'hod.ece@m3.com', 'dept': 'ECE'},
            
            # Faculty
            {'username': 'faculty_john', 'password': 'password123', 'role': 'FACULTY', 'email': 'john@m3.com', 'dept': 'CSE'},
            {'username': 'faculty_jane', 'password': 'password123', 'role': 'FACULTY', 'email': 'jane@m3.com', 'dept': 'ECE'},
        ]

        self.stdout.write('Creating test users...')
        
        for u in users:
            user, created = User.objects.get_or_create(username=u['username'], defaults={
                'email': u['email'],
                'role': u['role'],
                'department': u['dept']
            })
            
            if created:
                user.set_password(u['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created {u['role']}: {u['username']} / {u['password']}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {u['username']} already exists. Resetting password."))
                user.set_password(u['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Updated {u['username']} / {u['password']}"))

        self.stdout.write(self.style.SUCCESS('Test users ready.'))
