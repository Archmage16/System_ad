from rest_framework import serializers
from .models import Upload, Diploma


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = "__all__"


class DiplomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diploma
        fields = "__all__"