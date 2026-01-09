from rest_framework import serializers
from api.models import Computer, Office, Incident, Room

class ComputerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Computer
        fields = '__all__'
class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = '__all__'
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'