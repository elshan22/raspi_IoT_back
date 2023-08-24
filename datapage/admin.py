from django.contrib import admin

from .models import Temperature, Light

admin.site.register(Temperature)
admin.site.register(Light)
