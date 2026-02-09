from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Creates an admin user with username "admin" and password "admin123"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing admin user first',
        )

    def handle(self, *args, **options):
        if options['delete']:
            deleted_count, _ = User.objects.filter(username='admin').delete()
            if deleted_count > 0:
                self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} admin user(s)'))
            else:
                self.stdout.write(self.style.WARNING('No admin user found to delete'))
        
        if User.objects.filter(username='admin').exists():
            user = User.objects.get(username='admin')
            user.set_password('admin123')
            user.role = 'ADMIN'
            user.email = 'admin@university.edu'
            user.save()
            self.stdout.write(self.style.SUCCESS('Admin password reset to: admin123'))
        else:
            User.objects.create_user(
                username='admin',
                email='admin@university.edu',
                password='admin123',
                role='ADMIN'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))
