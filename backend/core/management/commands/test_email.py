from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = "Send a test email to verify SMTP configuration"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Recipient email address")

    def handle(self, *args, **options):
        recipient = options["email"]
        subject = "Timetable System: Test Email"
        message = "This is a test email from your Timetable Scheduling System. If you are receiving this, your SMTP configuration is correct!"
        
        self.stdout.write(f"Attempting to send test email to {recipient}...")
        self.stdout.write(f"Using Backend: {settings.EMAIL_BACKEND}")
        
        try:
            sent = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
            if sent:
                self.stdout.write(self.style.SUCCESS(f"Successfully sent test email to {recipient}"))
            else:
                self.stdout.write(self.style.WARNING("Email call returned 0 (not sent)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {str(e)}"))
            self.stdout.write("Please check your EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD in settings.py")
