"""
URL Configuration for Scheduler App

Author: Backend Team (Vamsi, Akshitha)
Sprint: 1
"""

from django.urls import path
from . import views

urlpatterns = [
    path('generate', views.trigger_generation, name='generate-schedule'),
    path('analytics/workload', views.get_workload_analytics, name='workload-analytics'),
    path('analytics/rooms', views.get_room_utilization, name='room-utilization'),
    path('timetable', views.get_timetable_view, name='timetable-view'),
]
