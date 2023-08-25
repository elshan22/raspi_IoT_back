import json

import paho.mqtt.client as mqtt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Task, ConditionalTask
from raspi.models import Node
from .serializers import TaskSerializer, ConditionalTaskSerializer


def on_connect(client, userdata, flags, rc):
    print('Connected to broker!')
    client.subscribe('raspi/actuators')


def on_message(client, userdata, message):
    json_object = json.loads(message.payload.decode())
    try:
        Node.objects.get(macaddress=json_object['mac_address'])
    except Node.DoesNotExist:
        Node.objects.create(macaddress=json_object['mac_address'], room=json_object['room'], type='AC')


def handle_every_day_schedule(request):
    return scheduler.add_job(blink_task(request['node_id'], request['blink_count'], request['blink_length']),
        trigger=CronTrigger(hour=request['hour'], minute=request['minute'], second=request['second']))


def handle_every_week_schedule(request):
    return scheduler.add_job(blink_task(request['node_id'], request['blink_count'], request['blink_length']),
        trigger=CronTrigger(day_of_week=request['weekday'][:3], hour=request['hour'],
                             minute=request['minute'], second=request['second']))


def handle_every_month_schedule(request):
    return scheduler.add_job(blink_task(request['node_id'], request['blink_count'], request['blink_length']),
        trigger=CronTrigger(day=request['day'], hour=request['hour'],
                            minute=request['minute'], second=request['second']))


def handle_every_year_schedule(request):
    return scheduler.add_job(blink_task(request['node_id'], request['blink_count'], request['blink_length']),
        trigger=CronTrigger(month=request['month'], day=request['day'], hour=request['hour'],
                            minute=request['minute'], second=request['second']))


def handle_just_once_schedule(request):
    return scheduler.add_job(blink_task(request['node_id'], request['blink_count'], request['blink_length']),
        trigger=CronTrigger(year=request['year'], month=request['month'], day=request['day'],
                            hour=request['hour'], minute=request['minute'], second=request['second']))


def handle_task_adding(request):
    if request['repeat'] == 'just-once':
        return handle_just_once_schedule(request)
    if request['repeat'] == 'every-day':
        return handle_every_day_schedule(request)
    if request['repeat'] == 'every-week':
        return handle_every_week_schedule(request)
    if request['repeat'] == 'every-month':
        return handle_every_month_schedule(request)
    return handle_every_year_schedule(request)


def set_tasks():
    tasks = Task.objects.all()
    for task in tasks:
        request = {'node_id': task.node.id, 'blink_count': task.blink_count,
                   'blink_length': task.blink_length, 'year': task.year,
                   'month': task.month, 'day': task.day, 'weekday': task.weekday,
                   'hour': task.exec_time.hour, 'minute': task.exec_time.minute,
                   'second': task.exec_time.second, 'repeat': task.repetition}
        job = handle_task_adding(request)
        task.job_id = job.id
        task.save()


def blink_task(node_id, count, duration):
    data = {'node_id': Node.objects.get(id=node_id).macaddress,
            'blink_length': duration,
            'blink_count': count}
    return lambda: client.publish('raspi/command', str(data))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('127.0.0.1', 1883)
client.subscribe('raspi/actuators')
client.loop_start()

scheduler = BackgroundScheduler()
scheduler.start()
set_tasks()


class CommandView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, internal_req=None):
        request = internal_req if internal_req else request.data
        try:
            node = Node.objects.get(id=request['node_id'])
            if node.type != 'AC':
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Node.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request['type'] == 'instant':
            request['node_id'] = Node.objects.get(id=request['node_id']).macaddress
            client.publish('raspi/command', str(request))
            return Response(status=status.HTTP_200_OK)
        if request['type'] == 'conditional':
            try:
                sensor = Node.objects.get(id=request['sensor'])
                if sensor.type != 'SE':
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                if not (node.room == sensor.room and node.sensor_type == sensor.sensor_type):
                    return Response(status=status.HTTP_403_FORBIDDEN)
                ConditionalTask.objects.create(sensor=sensor, actuator=node, blink_count=request['blink_count'],
                                            blink_length=request['blink_length'], value1=request['value1'],
                                            value2=request['value2'],
                                            condition=''.join([x[0].upper() for x in request['condition'].split('-')]))
                return Response(status=status.HTTP_201_CREATED)
            except Node.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        if request['type'] == 'add_task':
            job = handle_task_adding(request)
            Task.objects.create(node=Node.objects.get(id=request['node_id']), name=request['task_name'],
                                blink_count=request['blink_count'], blink_length=request['blink_length'],
                                exec_time=f'{request["hour"]}:{request["minute"]}:{request["second"]}',
                                year=request['year'], month=request['month'], day=request['day'],
                                weekday=request['weekday'], job_id=job.id,
                                repetition=''.join([x[0] for x in request['repeat'].split('-')]).upper())
            return Response(status=status.HTTP_201_CREATED)
        if request['type'] == 'remove_condition':
            try:
                request = request['data']
                ConditionalTask.objects.filter(id=request['id']).delete()
                return Response(status=status.HTTP_202_ACCEPTED)
            except ValueError:
                return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            request = request['data']
            Task.objects.filter(id=request['id']).delete()
            scheduler.remove_job(request['job_id'])
            return Response(status=status.HTTP_202_ACCEPTED)
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND)


class TasksView(APIView):
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        data = self.serializer_class(Task.objects.all(), many=True).data
        for d in data:
            node = Node.objects.get(id=d['node'])
            d['room'] = node.room
        return Response(data=data, status=status.HTTP_200_OK)


class ConditionalTasksView(APIView):
    serializer_class = ConditionalTaskSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        data = self.serializer_class(ConditionalTask.objects.all(), many=True).data
        for d in data:
            node = Node.objects.get(id=d['sensor'])
            d['room'] = node.room
        return Response(data=data, status=status.HTTP_200_OK)
