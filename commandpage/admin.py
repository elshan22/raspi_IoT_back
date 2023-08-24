from django.contrib import admin
from .models import Task, ConditionalTask

admin.site.register(Task)
admin.site.register(ConditionalTask)
