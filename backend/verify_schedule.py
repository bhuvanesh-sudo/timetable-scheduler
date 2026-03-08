import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()
from core.models import Schedule, ScheduleEntry, Teacher, Section

s = Schedule.objects.latest('created_at')
print("Schedule:", s.name)
print("Quality:", s.quality_score)

entries = ScheduleEntry.objects.filter(schedule=s).select_related('timeslot', 'course', 'section', 'teacher', 'room').order_by('timeslot__day', 'timeslot__slot_number')

# 1. Check for break crossings (Slots 2-3 and 5-6 should NOT be the same block)
print("\nChecking for break crossings...")
# We can check if any lab session or multi-slot theory has e.g. slot 2 and 3 for same (section, course)
# Actually, our algorithm creates individual entries. We need to check if (section, course) has 2 and 3 on same day.
bad_lab_crossings = []
for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
    day_entries = entries.filter(timeslot__day=day)
    sections = day_entries.values_list('section', flat=True).distinct()
    for sec_id in sections:
        sec_day_entries = day_entries.filter(section_id=sec_id)
        courses = sec_day_entries.values_list('course', flat=True).distinct()
        for c_id in courses:
            slots = set(sec_day_entries.filter(course_id=c_id).values_list('timeslot__slot_number', flat=True))
            if 2 in slots and 3 in slots:
                bad_lab_crossings.append(f"Section {sec_id} Course {c_id} day {day} slots 2 & 3")
            if 5 in slots and 6 in slots:
                bad_lab_crossings.append(f"Section {sec_id} Course {c_id} day {day} slots 5 & 6")

if not bad_lab_crossings:
    print("OK: No blocks cross Interval/Lunch!")
else:
    print("ERROR: Found some crossings:", bad_lab_crossings[:5])

# 2. Room Continuity (Theory back-to-back same room?)
print("\nChecking Room Continuity...")
matches = 0
total_back_to_back = 0
for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
    for sec in Section.objects.all():
        s_entries = entries.filter(timeslot__day=day, section=sec).order_by('timeslot__slot_number')
        for i in range(len(s_entries)-1):
            e1 = s_entries[i]
            e2 = s_entries[i+1]
            if e2.timeslot.slot_number == e1.timeslot.slot_number + 1:
                # Breaks at 2 and 5 should not allow continuity unless they are different slots
                if e1.timeslot.slot_number in [2, 5]: continue
                
                if not e1.is_lab_session and not e2.is_lab_session:
                    total_back_to_back += 1
                    if e1.room == e2.room:
                        matches += 1

if total_back_to_back > 0:
    print("Room continuity: " + str(matches) + "/" + str(total_back_to_back) + " (" + str(round(matches/total_back_to_back*100, 1)) + "%)")
else:
    print("No back-to-back theory classes found.")

# 3. Faculty Min Load (At least 2 classes per day if any)
print("\nChecking Faculty Min Load (>= 2 per day)...")
bad_load = 0
total_teaching_days = 0
for t in Teacher.objects.all():
    for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
        cnt = entries.filter(teacher=t, timeslot__day=day).count()
        if cnt > 0:
            total_teaching_days += 1
            if cnt < 2:
                bad_load += 1

if total_teaching_days > 0:
    print("Faculty min load (>=2): " + str(total_teaching_days - bad_load) + "/" + str(total_teaching_days) + " (" + str(round((total_teaching_days-bad_load)/total_teaching_days*100, 1)) + "%) success rate")
else:
    print("No teaching days found.")

# 4. Multiple labs on same day for section
print("\nChecking Section multi-lab per day...")
multi_lab = 0
for sec in Section.objects.all():
    for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
        lab_courses = entries.filter(section=sec, timeslot__day=day, is_lab_session=True).values_list('course', flat=True).distinct().count()
        if lab_courses > 1:
            multi_lab += 1
print("Sections with multi-lab on same day: " + str(multi_lab))
