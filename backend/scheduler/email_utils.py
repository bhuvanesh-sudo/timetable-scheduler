from django.core.mail import send_mass_mail
from django.conf import settings
from core.models import Schedule, ScheduleEntry, Teacher, TeacherCourseMapping, User
import logging

logger = logging.getLogger(__name__)

def send_publish_notifications(schedule_id, custom_messages=None):
    """
    Sends email notifications to all faculty members when a schedule is published.
    Direct/Synchronous implementation.
    
    Args:
        schedule_id: ID of the schedule being published
        custom_messages: Optional dict mapping teacher_id -> message string
    """
    try:
        schedule = Schedule.objects.get(pk=schedule_id)
        entries = ScheduleEntry.objects.filter(schedule=schedule).select_related('teacher')
        
        # Unique teachers in this schedule
        teachers = {e.teacher for e in entries if e.teacher.email}
        
        custom_messages = custom_messages or {}
        messages = []
        for teacher in teachers:
            subject = f"Timetable Updated: {schedule.name}"
            
            # Use custom message if provided, otherwise fallback to generic
            body_content = custom_messages.get(teacher.teacher_id)
            if not body_content:
                body_content = f"A new timetable '{schedule.name}' has been published.\nYou can view your classes by logging into the Timetable System."

            message = f"""Dear {teacher.teacher_name},

{body_content}

Semester: {schedule.semester}
Year: {schedule.year}

Regards,
Timetable Administration"""
            
            messages.append((subject, message, settings.DEFAULT_FROM_EMAIL, [teacher.email]))
        
        if messages:
            send_mass_mail(messages, fail_silently=False)
            logger.info(f"Sent {len(messages)} publication emails for schedule {schedule_id}")
            return f"Sent {len(messages)} emails"
        
        return "No emails to send"
        
    except Exception as e:
        logger.error(f"Error in send_publish_notifications: {str(e)}")
        return f"Error: {str(e)}"

def send_deadline_reminders(targeted=False):
    """
    Sends email reminders to faculty to submit their constraints/availability.
    If targeted=True, only sends to faculty who have NOT submitted any constraints.
    """
    try:
        teachers = Teacher.objects.exclude(email__isnull=True).exclude(email__exact='')

        if targeted:
            # Only remind faculty with no constraints submitted
            teachers_with_constraints = TeacherCourseMapping.objects.values_list(
                'teacher_id', flat=True
            ).distinct()
            teachers = teachers.exclude(teacher_id__in=teachers_with_constraints)

        if not teachers.exists():
            return "No faculty without constraints found." if targeted else "No faculty with email addresses found."
            
        messages = []
        for teacher in teachers:
            subject = "Action Required: Submit Your Timetable Constraints"
            message = f"""
Dear {teacher.teacher_name},

This is an automated reminder to log into the Timetable Scheduling System and submit your availability and constraints for the upcoming semester generation.

Please ensure your preferences are updated before the deadline so they can be considered by the scheduling algorithm.

Regards,
Timetable Administration
            """
            messages.append((subject, message, settings.DEFAULT_FROM_EMAIL, [teacher.email]))
        
        if messages:
            send_mass_mail(messages, fail_silently=False)
            logger.info(f"Sent {len(messages)} deadline reminder emails")
            return f"Sent {len(messages)} reminder emails"
            
        return "No emails to send"
        
    except Exception as e:
        logger.error(f"Error in send_deadline_reminders: {str(e)}")
        return f"Error: {str(e)}"
