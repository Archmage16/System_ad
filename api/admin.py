from django.contrib import admin
from api.models import Computer, Room, Office, Incident, TelegramProfile
# Register your models here.
admin.site.register(Computer)
admin.site.register(Room)
admin.site.register(Office)
admin.site.register(Incident)
admin.site.register(TelegramProfile)