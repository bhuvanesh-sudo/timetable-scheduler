from django.core.management.base import BaseCommand
from core.models import User, Teacher
from django.db import transaction

class Command(BaseCommand):
    help = 'Resets all users and creates standard Admin, HOD, and Faculty accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Resetting all user accounts...'))
        
        with transaction.atomic():
            # 1. Delete all existing users
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('  Deleted all existing users.'))

            # 2. Create Admin
            admin_email = "m3amrita+admin@gmail.com"
            User.objects.create_superuser(
                username='admin',
                user_id='admin',
                email=admin_email,
                password='admin123',
                first_name='Administrator', # Display Name
                role='ADMIN',
                is_protected=True
            )
            self.stdout.write(self.style.SUCCESS('  Created Admin: admin / admin123'))

            # 3. Create HOD
            hod_email = "m3amrita+hod@gmail.com"
            User.objects.create_user(
                username='hod',
                user_id='hod',
                email=hod_email,
                password='hod123',
                first_name='Head of Department', # Display Name
                role='HOD',
                department='CSE'
            )
            self.stdout.write(self.style.SUCCESS('  Created HOD: hod / hod123'))

            # 4. Create Faculty for all Teachers T001-T086
            teachers = Teacher.objects.all()
            self.stdout.write(f'  Processing {teachers.count()} teachers...')
            
            users_created = 0
            for teacher in teachers:
                tid_lower = teacher.teacher_id.lower()
                faculty_email = f"m3amrita+{tid_lower}@gmail.com"
                
                # Update teacher email in database
                teacher.email = faculty_email
                teacher.save()

                # Create user for teacher
                user = User.objects.create_user(
                    username=teacher.teacher_id,   # Login ID (T001 etc)
                    user_id=teacher.teacher_id,    # Unique ID
                    first_name=teacher.teacher_name, # Display Name
                    email=faculty_email,
                    password='faculty123',
                    role='FACULTY',
                    department=teacher.department
                )
                user.teacher = teacher
                user.save()
                users_created += 1

            self.stdout.write(self.style.SUCCESS(f'  Created {users_created} faculty accounts with password "faculty123"'))
            self.stdout.write(self.style.SUCCESS('Standard user setup complete.'))
