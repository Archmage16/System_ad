from django.urls import path
from api.views import *

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('', HomePage, name='home'),
    
    path('api/computers/', ComputerCreateView.as_view()),
    path('api/offices/', OfficeCreateView.as_view()),
    path('api/incidents/', IncidentCreateView.as_view()),
]
# 54321