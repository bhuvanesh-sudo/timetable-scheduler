from django.core.management.base import BaseCommand
from core.models import Teacher, User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Syncs existing Teachers with User accounts'

    def handle(self, *args, **options):
        self.stdout.write("Starting user sync for teachers...")
        
        teachers = Teacher.objects.all()
        created_count = 0
        linked_count = 0
        
        for teacher in teachers:
            # Check if user exists by username (Teacher ID)
            user = User.objects.filter(username=teacher.teacher_id).first()
            
            if not user:
                # Check by email as fallback
                user = User.objects.filter(email=teacher.email).first()
            
            if not user:
                # Create new user
                try:
                    user = User.objects.create_user(
                        username=teacher.teacher_id,
                        email=teacher.email,
                        password=f"{teacher.teacher_id}@123",
                        first_name=teacher.teacher_name.split(' ')[0],
                        last_name=' '.join(teacher.teacher_name.split(' ')[1:]),
                        role='FACULTY',
                        department=teacher.department,
                        teacher=teacher
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created user for {teacher.teacher_id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to create user for {teacher.teacher_id}: {e}"))
            else:
                # Ensure link exists
                if not user.teacher:
                    user.teacher = teacher
                    user.save()
                    linked_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Linked existing user to {teacher.teacher_id}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nSync Complete: Created {created_count}, Linked {linked_count}"))
