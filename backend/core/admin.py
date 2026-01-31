from django.contrib import admin
from .models import User, Block, Room, Department, Faculty, Course

admin.site.register(User)
admin.site.register(Block)
admin.site.register(Room)
admin.site.register(Department)
admin.site.register(Faculty)
admin.site.register(Course)
