import json
import socket
import time
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import NodeSerializer, LoginSerializer
from .models import Node
import subprocess
import re
from ping3 import ping
import paho.mqtt.client as mqtt
from datapage.models import Light, Temperature
from datapage.serializers import LightSerializer, TemperatureSerializer
from commandpage.models import Task, ConditionalTask
from commandpage.serializers import TaskSerializer, ConditionalTaskSerializer


f = open('info.json', 'r')
json_data = json.load(f)
f.close()


def update_data():
    nodes = NodeSerializer(Node.objects.all(), many=True).data
    lights = LightSerializer(Light.objects.all(), many=True).data
    temperatures = TemperatureSerializer(Temperature.objects.all(), many=True).data
    tasks = TaskSerializer(Task.objects.all(), many=True).data
    conditional_tasks = ConditionalTaskSerializer(ConditionalTask.objects.all(), many=True).data
    data = {'nodes': nodes, 'lights': lights, 'temperatures': temperatures, 'tasks': tasks,
            'conditional_tasks': conditional_tasks}
    client.publish(f'server/raspi{json_data["raspi"]}/main/2', str({'type': 'load', 'data': data}))


def on_connect(client, userdata, flags, rc):
    print('Connected to broker!')
    client.subscribe('server/raspi_hub/1')
    if json_data['raspi']:
        client.subscribe(f'server/raspi{json_data["raspi"]}/main/1')
    name = socket.gethostname()
    macaddress = re.findall('(([a-f0-9]{2}:){5}[a-f0-9]{2})', subprocess.check_output(
        'ip addr show | grep link/ether', shell=True, text=True).lower().split('\n')[0])[0][0]
    client.publish('server/raspi_hub/2', str({'name': name, 'macaddress': macaddress}))
    if json_data['raspi'] and json_data['user']:
        update_data()


def on_message(client, userdata, message):
    data = eval(message.payload.decode())
    if data['type'] == 'connect':
        json_data['raspi'] = data['raspi_id']
    else:
        if data['status'] == 'accepted':
            json_data['user'] = data['user']
        json_data['status'] = data['message']
    if json_data['user']:
        update_data()
    save_file()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message


def connect():
    try:
        global client
        client.connect('95.182.120.106', 1883)
        client.loop_start()
    except Exception:
        scheduler.add_job(connect, 'date', run_date=now() + timedelta(minutes=1))


scheduler = BackgroundScheduler()
scheduler.start()


connect()


def save_file():
    f = open('info.json', 'w')
    json.dump(json_data, f)
    f.close()


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(data={'status': json_data['status']}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            json_data['user'] = None
            save_file()
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if json_data['raspi']:
            request.data['type'] = 'connect'
            client.publish(f'server/raspi{json_data["raspi"]}/main/2', str(request.data))
        return Response(status=status.HTTP_200_OK)


class RaspberryPiInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if json_data['user']:
            client.publish(f'server/raspi{json_data["raspi"]}/main/2', str({'type': 'up_connect', 'id': json_data['user']['id']}))
        time.sleep(1)
        return Response(data={'raspi_name': socket.gethostname(), 'user': json_data['user']}, status=status.HTTP_200_OK)


class NodeView(APIView):
    serializer_class = NodeSerializer
    permission_classes = [AllowAny]

    def get(self, request, node_type):
        if node_type == 'all':
            nodes = Node.objects.all()
            devices = {x[1]: x[0] for x in re.findall('\((\\d+.\\d+.\\d+.\\d+)\).*(([0-9a-f]{2}:){5}[0-9a-f]{2}).*',
                subprocess.run(['arp', '-a'], capture_output=True, text=True).stdout.lower())}
            connections = {}
            for node in nodes:
                before = node.connected
                if node.macaddress.lower() not in devices:
                    node.connected = False
                else:
                    node.connected = ping(devices[node.macaddress.lower()]) is not None
                after = node.connected
                node.save()
                if not before == after:
                    connections[node.macaddress] = node.connected
            new_data = {'type': 'update', 'data': connections}
            if new_data['data'] and json_data['raspi']:
                client.publish(f'server/raspi{json_data["raspi"]}/main/2', str(new_data))
            data = self.serializer_class(nodes, many=True).data
        else:
            data = self.serializer_class(Node.objects.filter(type=node_type), many=True).data
        return Response(data=data, status=status.HTTP_200_OK)


class ThemeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(data={'theme': json_data['user']['dark'] if json_data['user'] else json_data['theme']}, status=status.HTTP_200_OK)

    def post(self, request):
        if json_data['user']:
            json_data['user']['dark'] = request.data['theme']
        else:
            json_data['theme'] = request.data['theme']
        data = {'type': 'change', 'theme': request.data['theme']}
        if json_data['user'] and json_data['raspi']:
            client.publish(f'server/raspi{json_data["raspi"]}/main/2', str(data))
        return Response(status=status.HTTP_200_OK)
