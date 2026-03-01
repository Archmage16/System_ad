# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadViewSet

router = DefaultRouter()
router.register(r'uploads', UploadViewSet, basename='upload')

urlpatterns = [
    path('generate/', UploadViewSet.as_view({'post': 'create'}), name='upload-generate'),
    path('', include(router.urls)),
]
