from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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



@login_required
def data_base_view(request):
    # Поиск по компьютерам
    query = request.GET.get('q', '')
    computers = Computer.objects.all()
    if query:
        computers = computers.filter(hostname__icontains=query)

    # Пагинация для компьютеров
    paginator = Paginator(computers.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'data': page_obj,           # Компьютеры для таблицы
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'Office': Office.objects.all(),    # Офисы для карточек
        'Room': Room.objects.all(),        # Комнаты для карточек
        'Incident': Incident.objects.all(),# Инциденты для таблицы
    }
    return render(request, 'dataCRUd/data_base.html', context)