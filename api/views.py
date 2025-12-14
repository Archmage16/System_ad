from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework import status, generics
from api.models import Room, Computer, Incident, Office
from api.serializers import ComputerSerializer, OfficeSerializer, IncidentSerializer

def HomePage(request):
    return render(request, 'index.html')



class OfficeCreateView(generics.CreateAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer

class IncidentCreateView(generics.CreateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer


def check_room_limit(room_id):
    room = Room.objects.get(id=room_id)
    current_count = Computer.objects.filter(room_id=room_id).count()
    return current_count < room.max_computers

class ComputerCreateView(generics.CreateAPIView):
    queryset = Computer.objects.all()
    serializer_class = ComputerSerializer

    def create(self, request, *args, **kwargs):
        room_id = request.data.get("room")

        if not check_room_limit(room_id):
            return Response(
                {"error": "This room is full"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

