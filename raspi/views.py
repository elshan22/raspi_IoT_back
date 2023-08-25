from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import NodeSerializer
from .models import Node
import subprocess
import re


darkMode = False


class RaspberryPiInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            username = subprocess.check_output(['whoami']).decode().strip()
            return Response(data={'name': username}, status=status.HTTP_200_OK)
        except subprocess.CalledProcessError as e:
            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)


class NodeView(APIView):
    serializer_class = NodeSerializer
    permission_classes = [AllowAny]

    def get(self, request, node_type):
        if node_type == 'all':
            data = self.serializer_class(Node.objects.all(), many=True).data
        else:
            data = self.serializer_class(Node.objects.filter(type=node_type), many=True).data
        return Response(data=data, status=status.HTTP_200_OK)


class NodeConnectionView(APIView):
    serializer_class = NodeSerializer
    permission_classes = [AllowAny]

    def get(self, request, node_id):
        try:
            node = Node.objects.get(id=node_id)
            data = self.serializer_class(node).data
            devices = subprocess.run(['arp', '-e'], capture_output=True, text=True).stdout
            data['connected'] = 'connected' if re.match(f'.*{node.macaddress}.*', devices) else 'disconnected'
            return Response(data=data, status=status.HTTP_200_OK)
        except subprocess.CalledProcessError:
            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
        except Node.DoesNotExist:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)


class ThemeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        global darkMode
        return Response(data={'theme': darkMode}, status=status.HTTP_200_OK)

    def post(self, request):
        global darkMode
        darkMode = request.data['theme']
        return Response(status=status.HTTP_200_OK)
