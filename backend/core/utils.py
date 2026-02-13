import csv
import io
from .models import Teacher, Section

class CSVImporter:
    """
    Utility for importing system data from CSV files with validation.
    """
    
    @staticmethod
    def import_teachers(csv_file):
        """
        Import teachers from CSV.
        Expected columns: teacher_id, teacher_name, email, department, max_hours_per_week
        """
        if not csv_file:
            raise ValueError("CSV file is empty or missing.")
            
        # If it's a string, wrap it in a StringIO
        if isinstance(csv_file, str):
            csv_file = io.StringIO(csv_file)
            
        reader = csv.DictReader(csv_file)
        
        # Validate columns
        required_columns = ['teacher_id', 'teacher_name', 'email', 'department', 'max_hours_per_week']
        if not all(col in reader.fieldnames for col in required_columns):
            missing = [col for col in required_columns if col not in reader.fieldnames]
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
            
        results = {'created': 0, 'updated': 0, 'errors': []}
        
        for row_idx, row in enumerate(reader, start=2):
            try:
                teacher_id = row['teacher_id'].strip()
                if not teacher_id:
                    results['errors'].append(f"Row {row_idx}: teacher_id is required.")
                    continue
                    
                # Validate max_hours is numeric
                try:
                    max_hours = int(row['max_hours_per_week'])
                except (ValueError, TypeError):
                    results['errors'].append(f"Row {row_idx}: max_hours_per_week must be an integer.")
                    continue
                
                teacher, created = Teacher.objects.update_or_create(
                    teacher_id=teacher_id,
                    defaults={
                        'teacher_name': row['teacher_name'].strip(),
                        'email': row['email'].strip(),
                        'department': row['department'].strip(),
                        'max_hours_per_week': max_hours
                    }
                )
                
                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1
                    
            except Exception as e:
                results['errors'].append(f"Row {row_idx}: {str(e)}")
                
        return results

    @staticmethod
    def import_sections(csv_file):
        """
        Import sections from CSV.
        Expected columns: class_id, year, section, department
        """
        if not csv_file:
            raise ValueError("CSV file is empty or missing.")
            
        if isinstance(csv_file, str):
            csv_file = io.StringIO(csv_file)
            
        reader = csv.DictReader(csv_file)
        
        required_columns = ['class_id', 'year', 'section', 'department']
        if not all(col in reader.fieldnames for col in required_columns):
            missing = [col for col in required_columns if col not in reader.fieldnames]
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
            
        results = {'created': 0, 'updated': 0, 'errors': []}
        
        for row_idx, row in enumerate(reader, start=2):
            try:
                class_id = row['class_id'].strip()
                if not class_id:
                    results['errors'].append(f"Row {row_idx}: class_id is required.")
                    continue
                
                try:
                    year = int(row['year'])
                except (ValueError, TypeError):
                    results['errors'].append(f"Row {row_idx}: year must be an integer.")
                    continue
                
                section_obj, created = Section.objects.update_or_create(
                    class_id=class_id,
                    defaults={
                        'year': year,
                        'section': row['section'].strip(),
                        'department': row['department'].strip(),
                    }
                )
                
                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1
                    
            except Exception as e:
                results['errors'].append(f"Row {row_idx}: {str(e)}")
                
        return results
