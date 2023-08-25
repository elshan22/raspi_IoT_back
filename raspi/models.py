import django.contrib.admin as admin
from django.db import models


class Node(models.Model):
    macaddress = models.CharField(max_length=30, unique=True)
    room = models.IntegerField()
    type = models.CharField(choices=(('AC', 'Actuator'), ('SE', 'Sensor')), max_length=10)
    sensor_type = models.CharField(max_length=20, null=True, blank=True)
    connected = models.BooleanField(default=False)


admin.site.register(Node)
