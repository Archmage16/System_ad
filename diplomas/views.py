# views.py
from rest_framework import viewsets
from .models import Upload
from .serializers import UploadSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .tasks import process_upload  # если используешь Celery

class UploadViewSet(viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer

    def perform_create(self, serializer):
        upload = serializer.save()  # сохраняем файл
        process_upload.delay(upload.id)  # асинхронная обработка