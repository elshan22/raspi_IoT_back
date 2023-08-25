import os
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import NodeSerializer
from .models import Node
import subprocess
import re
from ping3 import ping

darkMode = False


class RaspberryPiInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(data={'name': os.getlogin()}, status=status.HTTP_200_OK)


class NodeView(APIView):
    serializer_class = NodeSerializer
    permission_classes = [AllowAny]

    def get(self, request, node_type):
        if node_type == 'all':
            nodes = Node.objects.all()
            devices = {x[1]: x[0] for x in re.findall('\((\\d+.\\d+.\\d+.\\d+)\).*(([0-9a-f]{2}:){5}[0-9a-f]{2}).*',
                subprocess.run(['arp', '-a'], capture_output=True, text=True).stdout.lower())}
            for node in nodes:
                if node.macaddress.lower() not in devices:
                    node.connected = False
                else:
                    node.connected = ping(devices[node.macaddress.lower()]) is not None
                node.save()
            data = self.serializer_class(nodes, many=True).data
        else:
            data = self.serializer_class(Node.objects.filter(type=node_type), many=True).data
        return Response(data=data, status=status.HTTP_200_OK)


class ThemeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        global darkMode
        return Response(data={'theme': darkMode}, status=status.HTTP_200_OK)

    def post(self, request):
        global darkMode
        darkMode = request.data['theme']
        return Response(status=status.HTTP_200_OK)
