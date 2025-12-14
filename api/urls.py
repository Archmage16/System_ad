from django.urls import path
from api.views import *

urlpatterns = [
    path('', HomePage, name='home'),
    
    path('computers/create/', ComputerCreateView.as_view()),
    path('offices/create/', OfficeCreateView.as_view()),
    path('incidents/create/', IncidentCreateView.as_view()),
]
# 54321