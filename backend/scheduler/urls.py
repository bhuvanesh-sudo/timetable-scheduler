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
    path('my-schedule', views.get_my_schedule, name='my-schedule'),
    path('validate/<int:schedule_id>/', views.validate_schedule, name='validate-schedule'),
    path('validate-move', views.validate_move, name='validate-move'),
    path('move-entry', views.move_entry, name='move-entry'),
    path('publish/<int:schedule_id>/', views.publish_schedule, name='publish-schedule'),
    path('status/<int:schedule_id>/', views.get_schedule_status, name='schedule-status'),
    path('send-reminders/', views.send_reminders, name='send-reminders'),
]
