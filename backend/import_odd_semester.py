#!/usr/bin/env python
"""
Import odd semester data from CSV files into the database.
This script imports sections and ensures courses are available.
"""

import os
import sys
import django
import csv

# Setup Django
sys.path.append('/Users/Vamsi/Desktop/SE/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
django.setup()

from core.models import Section, Course

def import_odd_sections():
    """Import odd semester sections from classes_odd.csv"""
    csv_path = '/Users/Vamsi/Desktop/SE/Datasets/classes_odd.csv'
    
    print(f"Importing odd semester sections from {csv_path}...")
    
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        created_count = 0
        skipped_count = 0
        
        for row in reader:
            class_id = row['class_id']
            year = int(row['year'])
            sem = row['sem']
            
            # Check if section already exists
            if Section.objects.filter(class_id=class_id).exists():
                print(f"  ⏭️  Skipped {class_id} (already exists)")
                skipped_count += 1
                continue
            
            # Create section
            Section.objects.create(
                class_id=class_id,
                year=year,
                sem=sem,
                strength=60  # Default strength
            )
            print(f"  ✅ Created {class_id} - Year {year}, Semester: {sem}")
            created_count += 1
    
    print(f"\n✅ Import complete!")
    print(f"   Created: {created_count} sections")
    print(f"   Skipped: {skipped_count} sections (already existed)")
    
    # Verify
    total_odd = Section.objects.filter(sem='odd').count()
    print(f"\n📊 Total odd semester sections in database: {total_odd}")

def verify_odd_courses():
    """Verify that odd semester courses exist"""
    print("\n" + "="*60)
    print("Verifying odd semester courses...")
    
    odd_courses = Course.objects.filter(semester='odd')
    print(f"  Total odd semester courses: {odd_courses.count()}")
    
    if odd_courses.count() == 0:
        print("  ⚠️  WARNING: No odd semester courses found!")
        print("  You may need to import courses.csv")
    else:
        print("  ✅ Odd semester courses are available")
        
        # Show breakdown by year
        for year in [1, 2, 3, 4]:
            count = odd_courses.filter(year=year).count()
            print(f"     Year {year}: {count} courses")

if __name__ == '__main__':
    print("="*60)
    print("ODD SEMESTER DATA IMPORT")
    print("="*60)
    
    import_odd_sections()
    verify_odd_courses()
    
    print("\n" + "="*60)
    print("✅ All done! You can now generate schedules for odd semester.")
    print("="*60)
