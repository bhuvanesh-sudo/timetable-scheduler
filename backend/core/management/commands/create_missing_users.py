from django.core.management.base import BaseCommand
from core.models import Teacher
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates User accounts for any legacy Teacher records that do not have them.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        teachers_without_users = [t for t in Teacher.objects.all() if not User.objects.filter(teacher=t).exists()]
        count = 0

        for instance in teachers_without_users:
            if User.objects.filter(username=instance.teacher_id).exists():
                user = User.objects.get(username=instance.teacher_id)
                user.teacher = instance
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Linked existing user to {instance.teacher_id}"))
            else:
                try:
                    user = User.objects.create_user(
                        username=instance.teacher_id,
                        email=instance.email,
                        password=f"{instance.teacher_id}@123",
                        first_name=instance.teacher_name.split(' ')[0],
                        last_name=' '.join(instance.teacher_name.split(' ')[1:]),
                        role='FACULTY',
                        department=instance.department,
                        teacher=instance
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created new user for {instance.teacher_id}"))
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed for {instance.teacher_id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(teachers_without_users)} teachers. Created {count} missing user accounts."))
