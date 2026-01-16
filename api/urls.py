from django.urls import path
from api.views import *

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    path('', HomePage, name='home'),
    path('office_choose/', office_choose_view, name='office_choose'),
    path('data_base/', data_base_view, name='data_base'),
    path('reports/', reports_view, name='reports'),
    path('notes', notes_view, name='notes_view'),

    # path('api/u')
    path('api/computers/', ComputerCreateView.as_view(), name='computer-create'),
    path('api/tasks/', TaskCreateView.as_view(), name='task-create'),
    path('api/tasks/bot/', admin_tasks_bot, name='admin-tasks-bot'),
    path('api/offices/', OfficeCreateView.as_view(), name='office-create'),
    path('api/rooms/', RoomCreateView.as_view(), name='room-create'),
    path('api/rooms/bot/', AvailableRoomsView.as_view(), name='available-rooms'),
    path('api/incidents/', IncidentCreateView.as_view(), name='incident-create'),
    path('api/incidents/not-done/', not_done_incidents, name='not-done-incidents'),
    path('api/notes/', NotesView.as_view(), name='notes_api'),
    path("api/incidents/<int:incident_id>/close/", close_incident),

]
# 54321