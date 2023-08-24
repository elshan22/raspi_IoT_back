from rest_framework import serializers
from .models import Task, ConditionalTask


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class ConditionalTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionalTask
        fields = '__all__'
