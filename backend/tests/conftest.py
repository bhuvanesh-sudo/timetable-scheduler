"""
Pytest Configuration

Author: Test Team (Kanishthika)
Sprint: 1
"""

import pytest
import os
import django
from django.conf import settings

# Configure Django settings for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')

def pytest_configure():
    """Configure Django for pytest"""
    if not settings.configured:
        django.setup()
