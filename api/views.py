from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required

# rest.
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsSuperUserOrReadOnly
from rest_framework.response import Response
from rest_framework import status, generics
# api
from api.models import Room, Computer, Incident, Office
from api.serializers import ComputerSerializer, OfficeSerializer, IncidentSerializer

class UserLoginView(LoginView):
    template_name = 'login.html'
class UserLogoutView(LogoutView):
    next_page = '/login/'

@login_required
def HomePage(request):
    return render(request, 'index.html')



class OfficeCreateView(generics.ListCreateAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]


class IncidentCreateView(generics.ListCreateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]


def check_room_limit(room_id):
    room = Room.objects.get(id=room_id)
    current_count = Computer.objects.filter(room_id=room_id).count()
    return current_count < room.max_places
class ComputerCreateView(generics.ListCreateAPIView):
    queryset = Computer.objects.all()
    serializer_class = ComputerSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]

    def create(self, request, *args, **kwargs):
        room_id = request.data.get("room")

        if not check_room_limit(room_id):
            return Response(
                {"error": "This room is full"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)
