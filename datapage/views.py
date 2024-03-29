import json
from datetime import timedelta

import paho.mqtt.client as mqtt
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from commandpage.views import CommandView, scheduler
from raspi.models import Node
from .models import Light, Temperature
from .serializers import LightSerializer, TemperatureSerializer, LightReportSerializer, TemperatureReportSerializer
from commandpage.models import ConditionalTask
from raspi.views import json_data


def on_connect(client, userdata, flags, rc):
    print('Connected to broker!')
    client.subscribe('raspi/sensors')


def on_message(client, userdata, message):
    json_object = json.loads(message.payload.decode())
    if json_data['user']:
        server_client.publish(f'server/raspi{json_data["raspi"]}/sensors', message.payload.decode())
    try:
        node = Node.objects.get(macaddress=json_object['node_id'])
        if node.sensor_type == 'Temperature':
            Temperature.objects.create(node=node, temperature=json_object['current_temperature'])
            current = json_object['current_temperature']
        else:
            Light.objects.create(node=node, light=json_object['current_light'])
            current = json_object['current_light']
        tasks = ConditionalTask.objects.filter(sensor=node, condition='GT', value1__lte=current).union(
            ConditionalTask.objects.filter(sensor=node, condition='LT', value1__gte=current)).union(
            ConditionalTask.objects.filter(sensor=node, condition='BT', value1__lte=current, value2__gte=current))
        for task in tasks:
            CommandView().post({},
                               {'type': 'instant', 'node_id': task.actuator.id,
                                'blink_count': task.blink_count, 'blink_length': task.blink_length})
    except Node.DoesNotExist:
        Node.objects.create(macaddress=json_object['node_id'], room=json_object['room'], type='SE',
                            sensor_type=('Temperature' if 'current_temperature' in json_object else 'Light'))


def server_on_connect(client, userdata, flags, rc):
    print('Connected to broker!')


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883)
client.subscribe('raspi/sensors')
client.loop_start()

server_client = mqtt.Client()
server_client.on_connect = server_on_connect


def connect():
    try:
        global server_client
        server_client.connect('95.182.120.106', 1883)
        server_client.loop_start()
    except Exception:
        scheduler.add_job(connect, 'date', run_date=now() + timedelta(minutes=1))


connect()


class SensorView(APIView):
    light_serializer_class = LightSerializer
    temperature_serializer_class = TemperatureSerializer
    permission_classes = [AllowAny]

    def get(self, request, node_id):
        try:
            node = Node.objects.get(id=node_id)
            if node.type != 'SE':
                return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
            if node.sensor_type == 'Light':
                data = self.light_serializer_class(Light.objects.filter(node=node).latest('timestamp')).data
            else:
                data = self.temperature_serializer_class(Temperature.objects.filter(node=node).latest('timestamp')).data
            node = Node.objects.get(id=data['node'])
            data['type'] = node.sensor_type
            data['room'] = node.room
            return Response(data=data, status=status.HTTP_200_OK)
        except Node.DoesNotExist:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)


class DataView(APIView):
    light_serializer_class = LightReportSerializer
    temperature_serializer_class = TemperatureReportSerializer
    permission_classes = [AllowAny]

    def get(self, request, node_id, start_date, end_date):
        try:
            node = Node.objects.get(id=node_id)
            if node.type != 'SE':
                return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
            if node.sensor_type == 'Light':
                data = self.light_serializer_class(Light.objects.filter(node=node,
                                                                        timestamp__range=(start_date, end_date)),
                                                   many=True).data
            else:
                data = self.temperature_serializer_class(Temperature.objects.filter(node=node,
                                                                                    timestamp__range=(start_date, end_date)),
                                                         many=True).data
            return Response(data=data, status=status.HTTP_200_OK)
        except Node.DoesNotExist:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)
