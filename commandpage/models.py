from django.db import models
from raspi.models import Node


class Task(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    blink_count = models.IntegerField()
    blink_length = models.IntegerField()
    exec_time = models.TimeField()
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    weekday = models.CharField(max_length=10, null=True, blank=True)
    job_id = models.CharField(max_length=100)
    repetition = models.CharField(choices=(('JO', 'Just Once'),
                                           ('ED', 'Daily'),
                                           ('EW', 'Weekly'),
                                           ('EM', 'Monthly'),
                                           ('EY', 'Yearly')), max_length=10)


class ConditionalTask(models.Model):
    sensor = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='sensor_node')
    actuator = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='actuator_node')
    blink_count = models.IntegerField()
    blink_length = models.IntegerField()
    value1 = models.DecimalField(decimal_places=2, max_digits=8)
    value2 = models.DecimalField(decimal_places=2, max_digits=8, null=True, blank=True)
    condition = models.CharField(choices=(('LT', 'Less Than'), ('GT', 'Greater Than'), ('BT', 'Between')), max_length=10)
