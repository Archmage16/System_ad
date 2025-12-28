from django.urls import path
from api.views import *

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    path('', HomePage, name='home'),
    path('data_base/', data_base_view, name='data_base'),
    path('reports/', reports_view, name='reports'),

    # path('api/u')
    path('api/computers/', ComputerCreateView.as_view(), name='computer-create'),
    path('api/offices/', OfficeCreateView.as_view(), name='office-create'),
    path('api/incidents/', IncidentCreateView.as_view(), name='incident-create'),
]
# 54321