from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
# rest.
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsSuperUserOrReadOnly
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
# api
from api.models import Room, Computer, Incident, Office, TelegramProfile, Tasks, Notes
from api.serializers import ComputerSerializer, OfficeSerializer, IncidentSerializer, RoomSerializer, TaskSerializer, NoteSerializer
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

class TaskCreateView(generics.ListCreateAPIView):
    queryset = Tasks.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]

class RoomCreateView(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]
class AvailableRoomsView(generics.ListAPIView):
    """API для получения списка доступных комнат (для бота)"""
    queryset = Room.objects.select_related('office').all()
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]  # Разрешаем доступ без авторизации для бота
    
    def list(self, request, *args, **kwargs):
        rooms = self.get_queryset()
        serializer = self.get_serializer(rooms, many=True)
        
        # Форматируем данные для удобства в боте
        formatted_data = []
        for room in serializer.data:
            formatted_data.append({
                'id': room['id'],
                'room_number': room['room_number'],
                'office_name': room.get('office_name', ''),
                'full_name': f"{room.get('office_name', 'Офис')} - кабинет {room['room_number']}"
            })
        
        return Response(formatted_data)
class IncidentCreateView(generics.ListCreateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]

class NotesView(generics.ListCreateAPIView):
    queryset = Notes.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
@login_required
def notes_view(request):
    notes = Notes.objects.all().order_by('-created_at')
    paginator = Paginator(notes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'notes': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'dataCRUd/notes.html', context)

@api_view(['GET'])
def admin_tasks_bot(request):
    telegram_id = request.GET.get("telegram_id")

    if not telegram_id:
        return Response({"error": "telegram_id required"}, status=400)

    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
    except TelegramProfile.DoesNotExist:
        return Response({"error": "Access denied"}, status=403)

    if not profile.user.is_staff:
        return Response({"error": "Not admin"}, status=403)

    tasks = Tasks.objects.all().order_by("-created_at")
    serializer = TaskSerializer(tasks, many=True)

    return Response(serializer.data)

class IncidentCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = IncidentSerializer(data=request.data)
        if serializer.is_valid():
            incident = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def not_done_incidents(request):
    incidents = Incident.objects.filter(status__in=['new', 'in_progress'])
    serializer = IncidentSerializer(incidents, many=True)
    return Response(serializer.data)


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
    query = request.GET.get('q', '')
    computers = Computer.objects.all()
    if query:
        computers = computers.filter(hostname__icontains=query)
    paginator = Paginator(computers.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    Incidents = Incident.objects.filter(status__in=['new', 'in_progress']) # инцеиденты которые не готовы
    context = {
        'data': page_obj,        
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'Office': Office.objects.all(),    # Офисы для карточек
        'Room': Room.objects.all(),        # Комнаты для карточек
        'Incident': Incidents,# Инциденты для таблицы
    }
    return render(request, 'dataCRUd/data_base.html', context)

@login_required
def computer_by_room_view(request, room_id):
    computers = Computer.objects.filter(room_id=room_id)
    context = {'computers': computers}
    return render(request, 'dataCRUd/computers_by_room.html', context)
    
@login_required
def office_choose_view(request):
    offices = Office.objects.all()
    context = {'offices': offices}
    return render(request, 'dataCRUd/choose_office.html', context)
@login_required
def reports_view(request):
    inc = Incident.objects.all() 
    condition = len(inc)
    
    if condition == 0:
        status_s = "Amazing condition — no incidents recorded."
    elif condition < 10:
        status_s = "Normal condition — less than 10 incidents recorded."
    elif condition >= 10:
        status_s = "Bad condition — more than 10 incidents recorded."
    else:
        status_s = "No data available to determine condition."
    context = {'incidents': inc,
               'status_s': status_s}
    return render(request, 'dataCRUd/reports.html', context)

@api_view(['GET'])
def not_done_incidents(request):
    telegram_id = request.GET.get("telegram_id")

    if not telegram_id:
        return Response({"error": "telegram_id required"}, status=400)

    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
    except TelegramProfile.DoesNotExist:
        return Response({"error": "Access denied"}, status=403)

    if not profile.user.is_staff:
        return Response({"error": "Not admin"}, status=403)

    incidents = Incident.objects.exclude(status='done')
    serializer = IncidentSerializer(incidents, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def close_incident(request, incident_id):
    telegram_id = request.data.get("telegram_id")

    if not telegram_id:
        return Response({"error": "telegram_id required"}, status=400)

    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
    except TelegramProfile.DoesNotExist:
        return Response({"error": "Access denied"}, status=403)

    if not profile.user.is_staff:
        return Response({"error": "Not admin"}, status=403)

    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return Response({"error": "Incident not found"}, status=404)

    incident.status = "done"
    incident.closed_at = timezone.now()
    incident.save()

    return Response({"ok": True})