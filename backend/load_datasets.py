"""
Custom import script for actual dataset files:
  teachers1.csv + teachers2.csv  -> teachers (merged)
  courses.csv                    -> courses (tab-separated)
  rooms.csv                      -> rooms
  timeslots.csv                  -> timeslots
  classes.csv                    -> sections
  mapping1.csv + mapping2.csv    -> teacher-course mappings (just teacher_id, course_id, course_name)
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

import csv
from pathlib import Path
from core.models import (
    Teacher, Course, Room, TimeSlot, Section, TeacherCourseMapping,
    ScheduleEntry, Schedule, ConflictLog
)

BASE = Path(__file__).resolve().parent
DATASETS = BASE.parent / "Datasets"


def clear_data():
    print("Clearing existing data...")
    ScheduleEntry.objects.all().delete()
    Schedule.objects.all().delete()
    ConflictLog.objects.all().delete()
    TeacherCourseMapping.objects.all().delete()
    Section.objects.all().delete()
    TimeSlot.objects.all().delete()
    Room.objects.all().delete()
    Course.objects.all().delete()
    Teacher.objects.all().delete()
    print("  Done.")


def import_teachers():
    print("\nImporting teachers...")
    count = 0
    for fname in ["teachers1.csv", "teachers2.csv"]:
        fp = DATASETS / fname
        if not fp.exists():
            print(f"  Not found: {fname}")
            continue
        with open(fp, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Teacher.objects.update_or_create(
                    teacher_id=row["teacher_id"].strip(),
                    defaults={
                        "teacher_name": row["teacher_name"].strip(),
                        "email": row["email"].strip(),
                        "department": row["department"].strip(),
                        "max_hours_per_week": int(row["max_hours_per_week"]),
                    }
                )
                count += 1
    print(f"  ✓ {count} teachers imported")


def import_courses():
    print("\nImporting courses (tab-separated)...")
    count = 0
    fp = DATASETS / "courses.csv"
    if not fp.exists():
        print("  Not found: courses.csv")
        return
    with open(fp, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            course_id = row["course_id"].strip()
            if not course_id:
                continue
            Course.objects.update_or_create(
                course_id=course_id,
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
                    "is_project": bool(int(row["is_project"])),
                    "weekly_slots": int(row["weekly_slots"]),
                }
            )
            count += 1
    print(f"  ✓ {count} courses imported")


def import_rooms():
    print("\nImporting rooms...")
    count = 0
    fp = DATASETS / "rooms.csv"
    if not fp.exists():
        print("  Not found: rooms.csv")
        return
    with open(fp, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rt = row["room_type"].strip().upper()
            if rt == "LECTURE":
                rt = "CLASSROOM"
            Room.objects.update_or_create(
                room_id=row["room_id"].strip(),
                defaults={
                    "block": row["block"].strip(),
                    "floor": int(row["floor"]),
                    "room_type": rt,
                    "capacity": int(row.get("capacity", 60) or 60),
                }
            )
            count += 1
    print(f"  ✓ {count} rooms imported")


def import_timeslots():
    print("\nImporting timeslots...")
    count = 0
    from datetime import datetime
    fp = DATASETS / "timeslots.csv"
    if not fp.exists():
        print("  Not found: timeslots.csv")
        return
    with open(fp, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            TimeSlot.objects.update_or_create(
                slot_id=row["slot_id"].strip(),
                defaults={
                    "day": row["day"].strip(),
                    "slot_number": int(row["slot_number"]),
                    "start_time": datetime.strptime(row["start_time"].strip(), "%H:%M").time(),
                    "end_time": datetime.strptime(row["end_time"].strip(), "%H:%M").time(),
                }
            )
            count += 1
    print(f"  ✓ {count} timeslots imported")


def import_sections():
    print("\nImporting sections...")
    count = 0
    fp = DATASETS / "classes.csv"
    if not fp.exists():
        print("  Not found: classes.csv")
        return
    with open(fp, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            Section.objects.update_or_create(
                class_id=row["class_id"].strip(),
                defaults={
                    "year": int(row["year"]),
                    "section": row["section"].strip(),
                    "department": row["department"].strip(),
                }
            )
            count += 1
    print(f"  ✓ {count} sections imported")


def import_mappings():
    """
    mapping1.csv and mapping2.csv have columns: teacher_id, course_id, course_name
    No section or class_id — these are year-level mappings.
    """
    print("\nImporting teacher-course mappings...")
    count = 0
    skipped = 0
    for fname in ["mapping1.csv", "mapping2.csv"]:
        fp = DATASETS / fname
        if not fp.exists():
            print(f"  Not found: {fname}")
            continue
        with open(fp, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = row.get("teacher_id", "").strip()
                cid = row.get("course_id", "").strip()
                if not tid or not cid:
                    continue
                try:
                    teacher = Teacher.objects.get(teacher_id=tid)
                    course = Course.objects.get(course_id=cid)
                    # Use year-level mapping (no section)
                    TeacherCourseMapping.objects.update_or_create(
                        teacher=teacher,
                        course=course,
                        section=None,
                        year=course.year,
                        defaults={"preference_level": 3}
                    )
                    count += 1
                except (Teacher.DoesNotExist, Course.DoesNotExist) as e:
                    skipped += 1
    print(f"  ✓ {count} mappings imported, {skipped} skipped")


def summary():
    print("\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Teachers:  {Teacher.objects.count()}")
    print(f"Courses:   {Course.objects.count()}")
    print(f"Rooms:     {Room.objects.count()}")
    print(f"TimeSlots: {TimeSlot.objects.count()}")
    print(f"Sections:  {Section.objects.count()}")
    print(f"Mappings:  {TeacherCourseMapping.objects.count()}")
    print("="*50)


if __name__ == "__main__":
    clear_data()
    import_teachers()
    import_courses()
    import_rooms()
    import_timeslots()
    import_sections()
    import_mappings()
    summary()
    print("\n✓ All data imported successfully!")
