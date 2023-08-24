from rest_framework import serializers
from .models import Temperature, Light


class TemperatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Temperature
        fields = '__all__'


class TemperatureReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Temperature
        fields = ('temperature', 'time')


class LightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Light
        fields = '__all__'


class LightReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Light
        fields = ('light', 'time')
