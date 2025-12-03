from django.urls import path
from api.views import ComputerCreateView

urlpatterns = [
    path('computers/create/', ComputerCreateView.as_view()),
]
# 54321