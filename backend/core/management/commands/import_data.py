import os
import csv
from datetime import time
from django.core.management.base import BaseCommand
from core.models import Teacher, Course, Room, TimeSlot, Section, TeacherCourseMapping

class Command(BaseCommand):
    help = "Import initial data from CSV files in the Datasets folder"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before importing",
        )

    def handle(self, *args, **options):
        self.datasets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
            "Datasets",
        )

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            TeacherCourseMapping.objects.all().delete()
            Teacher.objects.all().delete()
            Course.objects.all().delete()
            Room.objects.all().delete()
            TimeSlot.objects.all().delete()
            Section.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("  ✓ Data cleared"))

        self.import_teachers()
        self.import_courses()
        self.import_rooms()
        self.import_timeslots()
        self.import_sections()
        self.import_teacher_course_mappings()
        self.print_summary()

    def import_teachers(self):
        """Import teachers from teachers.csv"""
        self.stdout.write("\nImporting teachers...")
        count = 0
        filename = "teachers.csv"
        filepath = os.path.join(self.datasets_path, filename)
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.WARNING(f"  File not found: {filename}"))
            return

        with open(filepath, "r") as file:
            content = file.read(2048)
            file.seek(0)
            dialect = csv.Sniffer().sniff(content) if ',' in content or '\t' in content else None
            reader = csv.DictReader(file, dialect=dialect) if dialect else csv.DictReader(file)
            for row in reader:
                Teacher.objects.update_or_create(
                    teacher_id=row["teacher_id"].strip(),
                    defaults={
                        "teacher_name": row["teacher_name"].strip(),
                        "email": row["email"].strip(),
                        "department": row["department"].strip(),
                        "max_hours_per_week": int(row["max_hours_per_week"]),
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} teachers"))

    def import_courses(self):
        """Import courses from courses.csv and electives.csv"""
        self.stdout.write("\nImporting courses...")
        count = 0

        # Regular courses
        filepath = os.path.join(self.datasets_path, "courses.csv")
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                content = file.read(2048)
                file.seek(0)
                dialect = csv.Sniffer().sniff(content) if ',' in content or '\t' in content else None
                reader = csv.DictReader(file, dialect=dialect) if dialect else csv.DictReader(file)
                for row in reader:
                    Course.objects.update_or_create(
                        course_id=row["course_id"].strip(),
                        defaults={
                            "course_name": row["course_name"].strip(),
                            "year": int(row["year"]),
                            "semester": row["semester"].strip().lower(),
                            "lectures": int(row["lectures"]),
                            "theory": int(row["theory"]),
                            "practicals": int(row["practicals"]),
                            "credits": int(row["credits"]),
                            "is_lab": bool(int(row["is_lab"])),
                            "is_elective": bool(int(row["is_elective"])),
                            "is_project": bool(int(row.get("is_project", 0))),
                            "weekly_slots": int(row["weekly_slots"]),
                        },
                    )
                    count += 1

        # Electives
        filepath_electives = os.path.join(self.datasets_path, "electives.csv")
        if os.path.exists(filepath_electives):
            with open(filepath_electives, "r") as file:
                content = file.read(2048)
                file.seek(0)
                dialect = csv.Sniffer().sniff(content) if ',' in content or '\t' in content else None
                reader = csv.DictReader(file, dialect=dialect) if dialect else csv.DictReader(file)
                for row in reader:
                    Course.objects.get_or_create(
                        course_id=row["course_id"].strip(),
                        defaults={
                            "course_name": row["course_name"].strip(),
                            "year": 1,
                            "semester": "odd",
                            "lectures": 3,
                            "theory": 3,
                            "practicals": 0,
                            "credits": 3,
                            "is_lab": False,
                            "is_elective": True,
                            "weekly_slots": 3,
                        },
                    )
                    count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} total courses"))

    def import_rooms(self):
        """Import rooms from rooms.csv"""
        self.stdout.write("\nImporting rooms...")
        filepath = os.path.join(self.datasets_path, "rooms.csv")
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR("  File not found: rooms.csv"))
            return
        count = 0
        with open(filepath, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                room_type_val = row["room_type"].upper()
                if room_type_val == "LECTURE":
                    room_type_val = "CLASSROOM"
                Room.objects.update_or_create(
                    room_id=row["room_id"].strip(),
                    defaults={
                        "block": row["block"].strip(),
                        "floor": int(row["floor"]),
                        "room_type": room_type_val,
                        "capacity": int(row.get("capacity", 60)),
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} rooms"))

    def import_timeslots(self):
        """Import timeslots from timeslots.csv"""
        self.stdout.write("\nImporting timeslots...")
        filepath = os.path.join(self.datasets_path, "timeslots.csv")
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR("  File not found: timeslots.csv"))
            return
        count = 0
        with open(filepath, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                start_h, start_m = map(int, row["start_time"].split(":"))
                end_h, end_m = map(int, row["end_time"].split(":"))
                TimeSlot.objects.update_or_create(
                    slot_id=row["slot_id"].strip(),
                    defaults={
                        "day": row["day"].strip(),
                        "slot_number": int(row["slot_number"]),
                        "start_time": time(start_h, start_m),
                        "end_time": time(end_h, end_m),
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} timeslots"))

    def import_sections(self):
        """Import sections from classes.csv"""
        self.stdout.write("\nImporting sections...")
        filepath = os.path.join(self.datasets_path, "classes.csv")
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR("  File not found: classes.csv"))
            return
        count = 0
        with open(filepath, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                Section.objects.update_or_create(
                    class_id=row["class_id"].strip(),
                    defaults={
                        "year": int(row["year"]),
                        "section": row["section"].strip(),
                        "department": row["department"].strip(),
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} sections"))

    def import_teacher_course_mappings(self):
        """Import mappings from oddMapping.csv and evenMapping.csv"""
        self.stdout.write("\nImporting teacher-course mappings...")
        count = 0
        skipped = 0
        for filename in ["oddMapping.csv", "evenMapping.csv"]:
            filepath = os.path.join(self.datasets_path, filename)
            if not os.path.exists(filepath):
                self.stdout.write(self.style.WARNING(f"  File not found: {filename}"))
                continue
            with open(filepath, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not row.get("teacher_id") or not row.get("course_id"):
                        continue
                    try:
                        teacher = Teacher.objects.get(teacher_id=row["teacher_id"].strip())
                        course = Course.objects.get(course_id=row["course_id"].strip())
                        TeacherCourseMapping.objects.update_or_create(
                            teacher=teacher,
                            course=course,
                            section=None,
                            year=course.year,
                            defaults={"preference_level": 3},
                        )
                        count += 1
                    except (Teacher.DoesNotExist, Course.DoesNotExist):
                        skipped += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} mappings (Skipped {skipped})"))

    def print_summary(self):
        """Print summary of imported data"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("DATA IMPORT SUMMARY"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"Teachers:                {Teacher.objects.count()}")
        self.stdout.write(f"Courses:                 {Course.objects.count()}")
        self.stdout.write(f"Rooms:                   {Room.objects.count()}")
        self.stdout.write(f"Time Slots:              {TimeSlot.objects.count()}")
        self.stdout.write(f"Sections:                {Section.objects.count()}")
        self.stdout.write(f"Mappings:                {TeacherCourseMapping.objects.count()}")
        self.stdout.write("=" * 50)
