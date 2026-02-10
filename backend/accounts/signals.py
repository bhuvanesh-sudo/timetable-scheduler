from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from core.models import Teacher, Course, Room, Section, Constraint, Schedule, AuditLog
from .middleware import get_current_user, get_current_request
import json

# List of models to track
TRACKED_MODELS = [Teacher, Course, Room, Section, Constraint, Schedule]

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def register_signals():
    for model in TRACKED_MODELS:
        post_save.connect(log_create_update, sender=model)
        post_delete.connect(log_delete, sender=model)

def log_create_update(sender, instance, created, **kwargs):
    user = get_current_user()
    # Don't log if no user (system action) or anonymous ??? 
    # Actually, we should log anonymous too if they managed to change something (security breach?)
    # But usually APIs are protected.
    
    request = get_current_request()
    ip_address = get_client_ip(request) if request else None
    
    action = 'CREATE' if created else 'UPDATE'
    
    # Simple serialization of instance
    try:
        # This is a bit simplistic, but good enough for now
        details = {
            'str': str(instance),
            # 'data': model_to_dict(instance) # Might be too verbose or fail on relations
        }
    except:
        details = {}

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        details=details,
        ip_address=ip_address
    )

def log_delete(sender, instance, **kwargs):
    user = get_current_user()
    request = get_current_request()
    ip_address = get_client_ip(request) if request else None
    
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action='DELETE',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        details={'str': str(instance)},
        ip_address=ip_address
    )

# Connect signals manually or in apps.py
# If I use @receiver on list, it's harder.
# register_signals() needs to be called.

@receiver(post_save, sender=Teacher)
def create_faculty_user(sender, instance, created, **kwargs):
    """
    Automatically create a User account for a new Teacher.
    Username: Teacher ID
    Password: TeacherID@123
    Role: FACULTY
    """
    if created:
        # Check if user already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.filter(username=instance.teacher_id).exists():
            try:
                # Create the user
                user = User.objects.create_user(
                    username=instance.teacher_id,
                    email=instance.email,
                    password=f"{instance.teacher_id}@123",  # Default password
                    first_name=instance.teacher_name.split(' ')[0],
                    last_name=' '.join(instance.teacher_name.split(' ')[1:]),
                    role='FACULTY',
                    department=instance.department,
                    teacher=instance
                )
                print(f"  [Auto-Create] Created user for {instance.teacher_id}")
            except Exception as e:
                print(f"  [Auto-Create] Failed to create user for {instance.teacher_id}: {e}")

