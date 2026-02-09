"""
Unit Tests for Module 2 - CSV Import

Tests the CSVImporter utility for correct data ingestion and error handling.
"""

import pytest
from core.utils import CSVImporter
from core.models import Teacher, Section

@pytest.mark.django_db
class TestCSVImport:
    """Test cases for CSV data import and validation"""

    def test_import_teachers_success(self):
        """Verify valid CSV imports successfully"""
        csv_data = (
            "teacher_id,teacher_name,email,department,max_hours_per_week\n"
            "T901,Prof. X,x@m3.com,CSE,15\n"
            "T902,Prof. Y,y@m3.com,ECE,18"
        )
        
        results = CSVImporter.import_teachers(csv_data)
        
        assert results['created'] == 2
        assert results['errors'] == []
        assert Teacher.objects.filter(teacher_id='T901').exists()

    def test_import_teachers_missing_column(self):
        """Verify missing required column raises error"""
        csv_data = "teacher_id,teacher_name,department\n"
        
        with pytest.raises(ValueError) as excinfo:
            CSVImporter.import_teachers(csv_data)
        assert "Missing required columns" in str(excinfo.value)

    def test_import_sections_duplicates(self):
        """Verify duplicate IDs results in updates"""
        csv_data = (
            "class_id,year,section,department\n"
            "SEC1,1,A,CSE\n"
            "SEC1,1,A,ECE"
        )
        
        results = CSVImporter.import_sections(csv_data)
        
        assert results['created'] == 1
        assert results['updated'] == 1
        assert Section.objects.count() == 1
        assert Section.objects.get(class_id='SEC1').department == 'ECE'
