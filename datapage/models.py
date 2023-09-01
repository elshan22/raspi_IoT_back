from django.db import models

from raspi.models import Node


class Temperature(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    temperature = models.DecimalField(decimal_places=2, max_digits=5)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)


class Light(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    light = models.DecimalField(decimal_places=2, max_digits=6)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)
